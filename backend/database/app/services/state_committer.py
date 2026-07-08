# -*- coding: utf-8 -*-
"""State Committer (ai-module-design §8)

Agent 输出的唯一落库通道。职责:
  1. 按 §8.1 校验 narrative 输出的 state_updates 合法性
  2. 按 §8.2 顺序在同一事务内写入; 任一步失败整体回滚
  3. 维护 clue_pressure / turns_since_key_clue 会话元数据

三个入口:
  commit_opening(session_id, opening)          开局落库
  commit_action(session_id, narrative, check, review)   每轮行动落库
  commit_report(session_id, summary)           结束报告落库 (+ finish 会话)
"""
import json
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from ..db.models import Character
from ..repositories import (ActionCheckRepo, AiReviewRepo, ClueRepo, FactRepo,
                            MessageRepo, NpcRepo, ReportRepo, SessionRepo,
                            TaskRepo)
from .clue_pressure import calc_clue_pressure

MAX_NPC_ALERT_DELTA = 3          # §8.1: NPC 警觉单次不超过 3
KEY_CLUE_PRESSURE_GATE = 0.6     # §8.1: key 线索需 clue_pressure>=0.6 或判定成功
SUCCESS_MARKERS = ("成功", "顺利", "毫不费力")
FAILURE_MARKERS = ("失败", "未能", "没能", "没有成功", "不成功", "落空")


class CommitError(Exception):
    """校验失败; 调用方据此回滚并走 fallback"""


@dataclass
class CommitResult:
    player_message_id: int | None = None
    dice_message_id: int | None = None
    narration_message_id: int | None = None
    check_id: int | None = None
    review_id: int | None = None
    new_clue_ids: list[int] = field(default_factory=list)
    new_fact_ids: list[int] = field(default_factory=list)
    touched_task_ids: list[int] = field(default_factory=list)
    clue_pressure: float = 0.0
    turns_since_key_clue: int = 0


class StateCommitter:
    def __init__(self, db: Session):
        self.db = db
        self.sessions = SessionRepo(db)
        self.messages = MessageRepo(db)
        self.clues = ClueRepo(db)
        self.facts = FactRepo(db)
        self.npcs = NpcRepo(db)
        self.checks = ActionCheckRepo(db)
        self.reviews = AiReviewRepo(db)
        self.tasks = TaskRepo(db)
        self.reports = ReportRepo(db)

    # ================= §8.1 校验 =================

    def _validate(self, session, narrative: dict, check: dict | None) -> None:
        updates = narrative.get("state_updates", {}) or {}
        character: Character = self.db.get(Character, session.character_id)

        # 1) HP: hp + hp_delta ∈ [0, max_hp]
        hp_delta = int(updates.get("hp_delta", 0) or 0)
        new_hp = character.hp + hp_delta
        if not 0 <= new_hp <= character.max_hp:
            raise CommitError(
                f"非法 hp_delta={hp_delta}: {character.hp} -> {new_hp} 超出 [0, {character.max_hp}]")

        # 2) key 线索门槛: clue_pressure>=0.6 或本轮判定成功
        check_success = bool(check and check.get("is_success"))
        for c in narrative.get("new_clues", []) or []:
            if c.get("importance") == "key" and not check_success \
                    and session.clue_pressure < KEY_CLUE_PRESSURE_GATE:
                raise CommitError(
                    f"key 线索[{c.get('title')}]被拒: clue_pressure="
                    f"{session.clue_pressure} < {KEY_CLUE_PRESSURE_GATE} 且判定未成功")

        # 3) hidden_truth 不得直升 player_known:
        #    a. new_facts 不允许出现受保护类型 (FactRepo 兜底, 此处提前拦截)
        #    b. player_known 新事实内容不得与既有 hidden_truth 实质重合
        hidden_contents = [
            f.content for f in self.facts.list_by_session(
                session.id, fact_types=["hidden_truth"])
        ]
        for f in updates.get("new_facts", []) or []:
            ftype = f.get("fact_type")
            if ftype in ("hidden_truth", "npc_private"):
                raise CommitError(f"AI new_facts 不得创建受保护类型: {ftype}")
            if ftype == "player_known":
                content = (f.get("content") or "").strip()
                for h in hidden_contents:
                    if content and (content in h or h in content):
                        raise CommitError(
                            "禁止将 hidden_truth 直接转为 player_known "
                            f"(命中: {h[:20]}...)")

        # 4) 规则一致: 判定失败时叙事不得描述完全成功 (轻量启发式, 语义层由 Critic 把关)
        if check is not None and check.get("is_success") is False:
            visible = narrative.get("visible_result", "") or ""
            if any(m in visible for m in SUCCESS_MARKERS) \
                    and not any(m in visible for m in FAILURE_MARKERS):
                raise CommitError(
                    f"判定失败但 visible_result 描述为成功: {visible[:40]}")

        # 5) NPC 警觉 delta 单次 <= 3
        for a in updates.get("npc_alertness", []) or []:
            if abs(int(a.get("delta", 0))) > MAX_NPC_ALERT_DELTA:
                raise CommitError(
                    f"npc_alertness delta 越界: {a.get('npc_id')} delta={a.get('delta')}")

        # 6) 场景: 必须非空字符串 (相邻性校验待 P1 场景图, MVP 只做基础检查)
        scene = updates.get("scene")
        if scene is not None and not str(scene).strip():
            raise CommitError("scene 不得为空字符串")

    # ================= 开局落库 =================

    def commit_opening(self, session_id: int, opening: dict) -> CommitResult:
        """写入: 开局旁白 message + 主任务 task + 会话场景/任务"""
        result = CommitResult()
        try:
            msg = self.messages.create(
                session_id, "ai", opening["narration"], "narration",
                tokens_used=opening.get("tokens_used"),
                latency_ms=opening.get("latency_ms"))
            result.narration_message_id = msg.id
            if opening.get("main_task"):
                task = self.tasks.create(session_id, opening["main_task"],
                                         opening.get("main_task_description"),
                                         status="doing")
                result.touched_task_ids.append(task.id)
            self.sessions.update_meta(
                session_id,
                scene=opening.get("scene_title"),
                current_task=opening.get("main_task"))
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise

    # ================= 每轮行动落库 (§8.2 顺序) =================

    def commit_action(
        self,
        session_id: int,
        user_id: int,
        action_text: str,
        narrative: dict,
        check: dict | None = None,
        review: dict | None = None,
    ) -> CommitResult:
        session = self.sessions.get_playing(session_id, user_id)
        if session is None:
            raise CommitError(f"进行中的会话 {session_id} 不存在或不属于用户 {user_id}")

        result = CommitResult()
        try:
            # ---- 校验先行, 不通过直接抛 CommitError ----
            self._validate(session, narrative, check)
            updates = narrative.get("state_updates", {}) or {}
            scene_for_check = updates.get("scene") or session.current_scene

            # 1. 玩家行动 message
            m1 = self.messages.create(session_id, "player", action_text, "action")
            result.player_message_id = m1.id

            # 2. action_checks (若有检定)
            if check is not None:
                ck = self.checks.create(
                    session_id, action_text, message_id=m1.id,
                    scene=scene_for_check,
                    check_type=check.get("check_type"),
                    skill_key=check.get("skill_key"),
                    attribute_used=check.get("attribute_used"),
                    dc=check.get("dc"), dice_roll=check.get("dice_roll"),
                    ability_modifier=check.get("ability_modifier"),
                    skill_bonus=check.get("skill_bonus", 0),
                    final_value=check.get("final_value"),
                    is_success=check.get("is_success"),
                    result_text=check.get("result_text"))
                result.check_id = ck.id
                # 3. system dice message
                m3 = self.messages.create(
                    session_id, "system", check.get("result_text", ""), "dice")
                result.dice_message_id = m3.id

            # 4. AI 旁白 message (+ tokens/latency)
            m4 = self.messages.create(
                session_id, "ai", narrative["narration"], "narration",
                tokens_used=narrative.get("tokens_used"),
                latency_ms=narrative.get("latency_ms"))
            result.narration_message_id = m4.id

            # 5. clues (去重在 ClueRepo)
            new_clues = self.clues.create_batch(
                session_id,
                [dict(c, source_scene=c.get("source_scene") or scene_for_check)
                 for c in narrative.get("new_clues", []) or []])
            result.new_clue_ids = [c.id for c in new_clues]

            # 6. facts (常规通道, 受保护类型已在校验拦截)
            for f in updates.get("new_facts", []) or []:
                fact = self.facts.create(
                    session_id, f["content"], f.get("fact_type", "session_fact"),
                    related_scene=f.get("related_scene") or scene_for_check,
                    importance=f.get("importance", "normal"))
                result.new_fact_ids.append(fact.id)

            # 6b. HP / NPC 警觉应用
            hp_delta = int(updates.get("hp_delta", 0) or 0)
            if hp_delta:
                character = self.db.get(Character, session.character_id)
                character.hp += hp_delta
            for a in updates.get("npc_alertness", []) or []:
                self.npcs.adjust_alertness(session_id, a["npc_id"], int(a["delta"]))

            # 7. tasks
            touched = self.tasks.update_batch(
                session_id, updates.get("task_updates", []) or [])
            result.touched_task_ids.extend(t.id for t in touched)

            # 8. game_sessions 元数据 (clue_pressure 依据本轮结果重算)
            got_key_clue = any(c.importance == "key" for c in new_clues)
            turns = 0 if got_key_clue else session.turns_since_key_clue + 1
            failed = self.checks.count_failed_in_scene(session_id, scene_for_check) \
                if scene_for_check else 0
            pressure = calc_clue_pressure(turns, failed)
            self.sessions.update_meta(
                session_id, scene=updates.get("scene"),
                summary_delta=updates.get("summary_delta"),
                clue_pressure=pressure, turns_since_key_clue=turns)
            result.clue_pressure = pressure
            result.turns_since_key_clue = turns

            # 9. ai_reviews
            if review is not None:
                rv = self.reviews.create(
                    session_id,
                    approved=bool(review.get("approved")),
                    overall_score=int(review.get("overall_score", 0)),
                    scores=review.get("scores"),
                    fatal_errors=review.get("fatal_errors"),
                    revision_instructions=review.get("revision_instructions"),
                    revision_count=int(review.get("revision_count", 0)),
                    used_fallback=bool(review.get("used_fallback")),
                    message_id=m4.id,
                    tokens_used=review.get("tokens_used"),
                    latency_ms=review.get("latency_ms"))
                result.review_id = rv.id

            self.db.commit()   # 同一事务提交
            return result
        except Exception:
            self.db.rollback()  # §8.2: 任一步失败整体回滚
            raise

    # ================= 结束报告落库 =================

    def commit_report(self, session_id: int, summary: dict,
                      finish_session: bool = True) -> int:
        """写入 reports (幂等 upsert); finish_session=True 时会话置 finished"""
        try:
            report = self.reports.upsert(
                session_id,
                title=summary.get("title"),
                story_summary=summary.get("story_summary"),
                key_choices=summary.get("key_choices"),
                clues=summary.get("clues"),
                ending_type=summary.get("ending_type"),
                character_growth=summary.get("character_growth"),
                ai_suggestion=summary.get("ai_suggestion"))
            if finish_session:
                self.sessions.finish(session_id)
            self.db.commit()
            return report.id
        except Exception:
            self.db.rollback()
            raise

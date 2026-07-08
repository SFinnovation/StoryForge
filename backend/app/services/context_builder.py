# -*- coding: utf-8 -*-
"""Context Builder (ai-module-design §3.3 / §6.3)

从 DB 读取并按可见性组装 Agent 上下文; 不调用 LLM。

四个入口:
  build_for_opening    开局 (读 worlds + characters)
  build_for_action     主 Agent 包 (§6.3; 不含完整 hidden_truth)
  build_for_critic     辅 Agent 包 (含 hidden_truth / npc forbidden_knowledge)
  build_for_summary    SummaryAgent 全局聚合
"""
import json
import os
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from backend.app.ai.schemas.character import CharacterCard, WorldContext
from backend.app.ai.schemas.opening import OpeningInput
from backend.app.models.models import ActionCheck, Character, Clue, Fact, GameSession, Message, World
from backend.app.repositories import (ActionCheckRepo, ClueRepo, MessageRepo,
                                      SessionRepo)
from backend.app.services.clue_pressure import CluePressureService
from backend.app.services.memory_retriever import MemoryRetriever

MESSAGE_LIMIT = int(os.getenv("AI_CONTEXT_MESSAGE_LIMIT", "20"))

# §6.3 主 Agent 恒定禁令
FORBIDDEN = [
    "不得透露 hidden_truth 中未解锁内容",
    "不得修改骰子结果",
    "不得替玩家做重大决定",
    "NPC 不得超出 knowledge_scope",
]


@dataclass
class ActionContext:
    world: WorldContext
    character: CharacterCard
    current_scene: str
    known_clues: list[str] = field(default_factory=list)
    clue_pressure: float = 0.0
    recent_summary: str = ""
    public_world_facts: list[str] = field(default_factory=list)
    hidden_truths: list[str] = field(default_factory=list)
    npc_private_facts: list[str] = field(default_factory=list)
    visible_npcs: list[dict] = field(default_factory=list)


def character_to_card(character: Character) -> CharacterCard:
    return CharacterCard(
        name=character.name,
        profession=character.class_id or "",
        background=character.background_id or "",
        motivation=character.motivation or "",
    )


class ContextBuilder:
    def __init__(self, db: Session):
        self.db = db
        self.sessions = SessionRepo(db)
        self.messages = MessageRepo(db)
        self.clues = ClueRepo(db)
        self.checks = ActionCheckRepo(db)
        self.memory = MemoryRetriever(db)
        self.pressure = CluePressureService(db)

    # ---------- 内部 ----------

    def _player_card(self, character: Character) -> dict:
        return {
            "name": character.name,
            "race_id": character.race_id,
            "class_id": character.class_id,
            "background_id": character.background_id,
            "motivation": character.motivation,
            "level": character.level,
            "hp": character.hp, "max_hp": character.max_hp,
            "proficiency_bonus": character.proficiency_bonus,
            "abilities": {
                "strength": character.strength, "dexterity": character.dexterity,
                "constitution": character.constitution, "intelligence": character.intelligence,
                "wisdom": character.wisdom, "charisma": character.charisma,
            },
            "skills": json.loads(character.skills_json or "{}"),
            "saving_throws": json.loads(character.saving_throws_json or "[]"),
            "inventory": json.loads(character.inventory_json or "[]"),
        }

    # ---------- 开局 ----------

    def build_for_opening(self, world_id: int, character_id: int) -> dict:
        world = self.db.get(World, world_id)
        character = self.db.get(Character, character_id)
        if world is None or character is None:
            raise ValueError("world 或 character 不存在")
        return {
            "role": "OpeningAgent",
            "world": {
                "name": world.name, "type": world.type,
                "description": world.description,
                "opening_prompt": world.opening_prompt,   # AI 开局 system 上下文
                "rule_style": world.rule_style, "difficulty": world.difficulty,
            },
            "player_card": self._player_card(character),
            "forbidden": FORBIDDEN,
        }

    # ---------- 主 Agent (§6.3) ----------

    def build_for_action(self, session_id: int, rule_result: dict | None,
                         action_text: str) -> dict:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError(f"session {session_id} 不存在")
        world = self.db.get(World, session.world_id)
        character = self.db.get(Character, session.character_id)
        pressure = self.pressure.calculate(session_id)
        hidden = self.memory.get_hidden_truths(session_id)

        return {
            "role": "NarrativeAgent",
            "world_style": world.type if world else None,
            "public_world_facts": [f.content for f in
                                   self.memory.get_world_public_facts(session_id)],
            "current_scene": {"name": session.current_scene,
                              "task": session.current_task},
            "player_card": self._player_card(character),
            "recent_summary": session.summary,
            "recent_messages": [
                {"sender": m.sender_type, "type": m.message_type, "content": m.content}
                for m in self.messages.list_recent(session_id, MESSAGE_LIMIT)
            ],
            "player_known_clues": [
                {"title": c.title, "content": c.content, "importance": c.importance}
                for c in self.clues.list_by_session(session_id)
            ],
            "player_known_facts": [f.content for f in
                                   self.memory.get_player_known_facts(session_id)],
            "visible_npcs": self.memory.get_visible_npcs(session_id, session.current_scene),
            # §4.1: 主 Agent 对 hidden_truth 仅见"存在摘要", 不见内容
            "hidden_truth_summary": f"本会话存在 {len(hidden)} 条隐藏真相, 禁止编造或透露",
            "player_action": action_text,
            "rule_result": rule_result or {},
            "clue_pressure": pressure.clue_pressure,
            "clue_pressure_tier": pressure.tier,
            "forbidden": FORBIDDEN,
        }

    # ---------- 辅 Agent (§3.5 特权可见) ----------

    def build_for_critic(self, session_id: int, narrative_output: dict,
                         rule_result: dict | None) -> dict:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError(f"session {session_id} 不存在")
        return {
            "role": "CriticAgent",
            "narrative_output": narrative_output,
            "rule_result": rule_result or {},
            "current_scene": session.current_scene,
            "recent_messages": [
                {"sender": m.sender_type, "content": m.content}
                for m in self.messages.list_recent(session_id, MESSAGE_LIMIT)
            ],
            # 特权: 完整 hidden_truth + npc_private + NPC 禁区, 用于泄露检测
            "hidden_truths": [
                {"id": f.id, "content": f.content, "status": f.status}
                for f in self.memory.get_hidden_truths(session_id)
            ],
            "npc_private_facts": [f.content for f in
                                  self.memory.get_npc_private_facts(session_id)],
            "npc_boundaries": self.memory.get_npc_boundaries(session_id),
        }

    # ---------- SummaryAgent ----------

    def build_for_summary(self, session_id: int) -> dict:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError(f"session {session_id} 不存在")
        all_msgs = self.messages.list_all(session_id)
        return {
            "role": "SummaryAgent",
            "title": session.title,
            "summary": session.summary,
            "player_actions": [m.content for m in all_msgs if m.sender_type == "player"],
            "ai_narrations": [m.content for m in all_msgs if m.sender_type == "ai"],
            "checks": [
                {"action": c.action_text, "type": c.check_type, "dc": c.dc,
                 "final": c.final_value, "success": bool(c.is_success)}
                for c in self.checks.list_by_session(session_id)
            ],
            "clues": [
                {"title": c.title, "importance": c.importance}
                for c in self.clues.list_by_session(session_id)
            ],
        }


def build_for_opening(db: Session, world: World, character: Character) -> OpeningInput:
    return OpeningInput(
        world=WorldContext(
            name=world.name,
            description=world.description or "",
            style=world.type or "",
            opening_prompt=world.opening_prompt or "",
        ),
        character=character_to_card(character),
    )


def build_for_action(db: Session, session: GameSession) -> ActionContext:
    world = db.get(World, session.world_id)
    character = db.get(Character, session.character_id)
    if world is None or character is None:
        raise ValueError("session world or character missing")

    clues = (
        db.query(Clue)
        .filter(Clue.session_id == session.id)
        .order_by(Clue.discovered_at.desc())
        .limit(20)
        .all()
    )
    facts_player = (
        db.query(Fact)
        .filter(Fact.session_id == session.id, Fact.fact_type == "player_known")
        .all()
    )
    facts_public = (
        db.query(Fact)
        .filter(Fact.session_id == session.id, Fact.fact_type == "world_public")
        .all()
    )
    recent_msgs = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.id.desc())
        .limit(10)
        .all()
    )
    recent_summary = session.summary or ""
    if not recent_summary and recent_msgs:
        recent_summary = " | ".join(m.content[:80] for m in reversed(recent_msgs))

    memory = MemoryRetriever(db)
    return ActionContext(
        world=WorldContext(
            name=world.name,
            description=world.description or "",
            style=world.type or "",
            opening_prompt=world.opening_prompt or "",
        ),
        character=character_to_card(character),
        current_scene=session.current_scene or world.name,
        known_clues=[c.title for c in clues],
        clue_pressure=float(session.clue_pressure or 0.0),
        recent_summary=recent_summary,
        public_world_facts=[f.content for f in facts_public + facts_player],
        hidden_truths=[f.content for f in memory.get_hidden_truths(session.id)],
        npc_private_facts=[f.content for f in memory.get_npc_private_facts(session.id)],
        visible_npcs=memory.get_visible_npcs(session.id, session.current_scene),
    )


def build_for_summary(db: Session, session: GameSession):
    from backend.app.ai.schemas import CheckResult, SummaryInput

    character = db.get(Character, session.character_id)
    world = db.get(World, session.world_id)
    if character is None or world is None:
        raise ValueError("session world or character missing")

    checks = db.query(ActionCheck).filter(ActionCheck.session_id == session.id).all()
    return SummaryInput(
        world=WorldContext(
            name=world.name,
            description=world.description or "",
            style=world.type or "",
            opening_prompt=world.opening_prompt or "",
        ),
        character=character_to_card(character),
        player_actions=[
            m.content
            for m in db.query(Message)
            .filter(Message.session_id == session.id, Message.message_type == "action")
            .order_by(Message.id)
            .all()
        ],
        check_results=[
            CheckResult(
                success=bool(c.is_success),
                dice_roll=c.dice_roll,
                final_value=c.final_value,
                dc=c.dc,
                check_type=c.check_type,
                attribute_used=c.attribute_used,
                result_text=c.result_text,
            )
            for c in checks
        ],
        ai_narrations=[
            m.content
            for m in db.query(Message)
            .filter(Message.session_id == session.id, Message.message_type == "narration")
            .order_by(Message.id)
            .all()
        ],
        discovered_clues=[
            c.title for c in db.query(Clue).filter(Clue.session_id == session.id).all()
        ],
        session_summary=session.summary or "",
    )

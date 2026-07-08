# -*- coding: utf-8 -*-
"""Repository 层验证 — 模拟一轮行动的完整读写路径

覆盖 ai-module-design §11.1 全部 8 个 Repository:
  开局: NpcRepo.create_batch + FactRepo.create(allow_protected)
  行动: MessageRepo -> ActionCheckRepo -> ClueRepo -> FactRepo -> TaskRepo
        -> SessionRepo.update_meta -> AiReviewRepo
  校验: Fact 可见性裁剪 / hidden_truth 保护 / 线索去重 / 场景失败计数

用法: cd backend && python -m scripts.verify_repositories
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.database import SessionLocal
from backend.app.repositories import (ActionCheckRepo, AiReviewRepo, ClueRepo,
                              FactRepo, MessageRepo, NpcRepo, SessionRepo,
                              TaskRepo)

PASS = "  [PASS]"


def main() -> None:
    db = SessionLocal()
    try:
        sessions = SessionRepo(db)
        messages = MessageRepo(db)
        clues = ClueRepo(db)
        facts = FactRepo(db)
        npcs = NpcRepo(db)
        checks = ActionCheckRepo(db)
        reviews = AiReviewRepo(db)
        tasks = TaskRepo(db)

        # ---- 0. 取种子会话 ----
        s = sessions.get_playing(1, user_id=1)
        assert s is not None, "种子会话不存在, 先跑 init_db + seed_data"
        print(f"会话: {s.title} (scene={s.current_scene})")

        # ---- 1. 开局 seed: NPC + 分层 Fact ----
        npcs.create_batch(s.id, [dict(
            npc_id="lavinia_001", name="纳休斯·文",
            personality="拘谨、回避审问相关问题",
            knowledge_scope=["委托内容", "预付金"],
            forbidden_knowledge=["幕后雇主身份"],
            speaking_style="正式、官腔", related_scene="锯齿监狱·会见纳休斯",
        )])
        facts.create(s.id, "十会盟悬赏活捉克仑可", "world_public")
        hidden = facts.create(s.id, "克仑可藏身锻炉街运河码头旧仓库", "hidden_truth",
                              importance="key", status="locked", allow_protected=True)
        print(PASS, "world_seed 路径: NPC + world_public + hidden_truth 写入")

        # ---- 2. Fact 可见性裁剪 (§1.2 硬约束 3) ----
        player_view = facts.list_by_session(s.id, visibility="player")
        assert all(f.fact_type != "hidden_truth" for f in player_view), "hidden_truth 泄露给玩家视图!"
        critic_view = facts.list_by_session(s.id, fact_types=["hidden_truth", "npc_private"])
        assert any(f.id == hidden.id for f in critic_view)
        print(PASS, f"可见性裁剪: 玩家视图 {len(player_view)} 条(无 hidden), Critic 视图含完整 hidden_truth")

        # ---- 3. hidden_truth 保护通道 ----
        try:
            facts.create(s.id, "AI 私自造隐藏真相", "hidden_truth")
            raise AssertionError("保护失效")
        except PermissionError:
            print(PASS, "常规通道创建 hidden_truth 被拒绝 (仅 world_seed 允许)")

        # ---- 4. 一轮行动的写入顺序 (§8.2) ----
        scene = "广场西下水道"
        m1 = messages.create(s.id, "player", "我检查被撬开的格栅", "action")
        ck = checks.create(s.id, "检查格栅", message_id=m1.id, scene=scene,
                           check_type="察觉", skill_key="prc", attribute_used="wisdom",
                           dc=10, dice_roll=4, ability_modifier=1, skill_bonus=0,
                           final_value=5, is_success=False,
                           result_text="d20(4)+感知(+1)=5 < DC10, 失败")
        messages.create(s.id, "system", ck.result_text, "dice")
        m4 = messages.create(s.id, "ai", "锈蚀的格栅纹丝不动, 黑暗中传来水声……",
                             "narration", tokens_used=850, latency_ms=2100)
        new = clues.create_batch(s.id, [
            dict(title="井下的靴印", content="通向锻炉街方向", importance="important"),
            dict(title="井下的靴印", content="重复项应被跳过"),
        ])
        assert len(new) == 1, "线索去重失败"
        facts.create(s.id, "玩家已发现下水道入口被撬", "session_fact")
        tasks.update_batch(s.id, [dict(title="活捉克仑可", status="doing")])
        sessions.update_meta(s.id, scene=scene, summary_delta="检查格栅失败。",
                             clue_pressure=0.25, turns_since_key_clue=1)
        reviews.create(s.id, approved=True, overall_score=86,
                       scores={"rule_consistency": 90, "npc_knowledge_boundary": 88},
                       message_id=m4.id, revision_count=0)
        db.commit()
        print(PASS, "§8.2 写入顺序 9 步全部落库并提交")

        # ---- 5. 读路径回验 ----
        assert len(messages.list_recent(s.id, limit=20)) >= 4
        assert checks.count_failed_in_scene(s.id, scene) == 1
        assert sessions.get(s.id).clue_pressure == 0.25
        assert npcs.list_visible(s.id, "锯齿监狱·会见纳休斯")[0].name == "纳休斯·文"
        assert reviews.list_recent(s.id)[0].overall_score == 86
        assert facts.unlock(hidden.id).status == "active"
        db.commit()
        print(PASS, "读路径: list_recent / count_failed_in_scene / list_visible / unlock 全部正确")

        # ---- 6. 事务回滚 (§8.2: 失败整体回滚) ----
        before = len(messages.list_all(s.id))
        try:
            messages.create(s.id, "player", "回滚测试", "action")
            messages.create(s.id, "bad_sender", "非法", "action")  # 触发 ValueError
        except ValueError:
            db.rollback()
        assert len(messages.list_all(s.id)) == before, "回滚失败, 出现半截数据"
        print(PASS, "事务回滚: 中途失败不留半截数据")

        print("\n全部通过 — Repository 层与 §11.1 接口清单一致")
    finally:
        db.close()


if __name__ == "__main__":
    main()

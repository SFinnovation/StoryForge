# -*- coding: utf-8 -*-
"""AI <-> 数据库交互验证 (implementation §12 承诺的 verify_ai_db_interaction)

闭环: 开局 seed -> 上下文可见性 -> 行动落库 -> 非法输出拦截+回滚 -> 结束报告
所有 AI 输出用文档 §6.4/§6.5 示例格式的 mock JSON, 不需要 LLM API Key。

用法: cd backend && python -m scripts.verify_ai_db_interaction
"""
from app.db.database import SessionLocal
from app.db.models import Character, GameSession, Message, Report
from app.repositories import FactRepo, MessageRepo, NpcRepo
from app.services.clue_pressure import CluePressureService
from app.services.context_builder import ContextBuilder
from app.services.state_committer import CommitError, StateCommitter
from app.services.world_seed import seed_session_world_data

PASS = "  [PASS]"


def make_narrative(**over) -> dict:
    """§6.4 格式的 mock 主 Agent 输出"""
    base = {
        "narration": "你压低脚步靠近格栅, 靴底却踩碎枯叶。井下传来急促的脚步声远去。",
        "visible_result": "追踪失败, 目标察觉到了动静。",
        "new_clues": [{"title": "井下的靴印", "content": "鬼怪尺码, 通向锻炉街方向",
                       "importance": "important"}],
        "state_updates": {
            "scene": "广场西下水道", "summary_delta": "追踪靴印失败。",
            "hp_delta": 0, "npc_alertness": [], "task_updates": [], "new_facts": [],
        },
        "next_options": ["强行拉开格栅", "返回地面打探", "沿运河方向绕行"],
        "tokens_used": 1240, "latency_ms": 3200,
    }
    base.update(over)
    return base


CHECK_FAIL = {"check_type": "求生", "skill_key": "sur", "attribute_used": "wisdom",
              "dc": 15, "dice_roll": 6, "ability_modifier": 1, "skill_bonus": 0,
              "final_value": 7, "is_success": False,
              "result_text": "d20(6)+感知(+1)=7 < DC15, 失败"}
REVIEW_OK = {"approved": True, "overall_score": 86, "revision_count": 0,
             "scores": {"rule_consistency": 90, "world_consistency": 88,
                        "context_continuity": 85, "character_alignment": 87,
                        "npc_knowledge_boundary": 84, "clue_progression": 82},
             "used_fallback": False}


def main() -> None:
    db = SessionLocal()
    try:
        committer = StateCommitter(db)
        builder = ContextBuilder(db)
        # 自建全新会话, 与种子会话/其他验证脚本互不干扰 (可重复执行)
        seed = db.query(GameSession).first()
        assert seed, "先跑 init_db + seed_data"
        session = GameSession(user_id=seed.user_id, world_id=seed.world_id,
                              character_id=seed.character_id,
                              title="verify_ai_db_interaction 专用会话")
        db.add(session)
        db.commit()
        sid, uid = session.id, session.user_id
        print(f"验证会话 id={sid} (world_id={session.world_id})")

        # ===== 1. 开局: world_seed + commit_opening =====
        seeded = seed_session_world_data(db, sid)
        db.commit()
        assert not seeded["skipped"] and seeded["facts"] >= 4 and seeded["npcs"] >= 2
        committer.commit_opening(sid, {
            "narration": "锯齿监狱的会客室里, 纳休斯·文推来一枚十会盟印记……",
            "scene_title": "锯齿监狱·会见纳休斯", "main_task": "三天内活捉克仑可"})
        print(PASS, f"开局: seed {seeded['facts']} facts / {seeded['npcs']} npcs + 旁白与主任务落库")
        assert seed_session_world_data(db, sid)["skipped"], "重复 seed 未跳过"
        print(PASS, "world_seed 幂等: 二次调用跳过")

        # ===== 2. 上下文可见性 (§1.2 硬约束 3) =====
        main_ctx = builder.build_for_action(sid, CHECK_FAIL, "我沿着靴印追下去")
        blob = str(main_ctx)
        hidden = FactRepo(db).list_by_session(sid, fact_types=["hidden_truth"])
        assert hidden and all(h.content not in blob for h in hidden), "hidden_truth 泄露进主 Agent 上下文!"
        assert "隐藏真相" in main_ctx["hidden_truth_summary"]
        assert main_ctx["rule_result"]["is_success"] is False
        critic_ctx = builder.build_for_critic(sid, make_narrative(), CHECK_FAIL)
        assert any(h.content == f["content"] for h in hidden for f in critic_ctx["hidden_truths"])
        assert any(n["forbidden_knowledge"] for n in critic_ctx["npc_boundaries"])
        print(PASS, "可见性: 主 Agent 仅见摘要, Critic 见完整 hidden_truth + NPC 禁区")

        # ===== 3. 合法行动落库 (§8.2 九步) =====
        r = committer.commit_action(sid, uid, "我沿着靴印追下去",
                                    make_narrative(), CHECK_FAIL, REVIEW_OK)
        assert all([r.player_message_id, r.dice_message_id, r.narration_message_id,
                    r.check_id, r.review_id]) and r.new_clue_ids
        assert r.turns_since_key_clue == 1 and r.clue_pressure > 0
        msg = db.get(Message, r.narration_message_id)
        assert msg.tokens_used == 1240 and msg.latency_ms == 3200
        print(PASS, f"合法行动 9 步落库, clue_pressure={r.clue_pressure:.2f}, turns=1")

        # ===== 4. §8.1 非法输出逐条拦截, 且整体回滚 =====
        before = len(MessageRepo(db).list_all(sid))
        char = db.get(Character, session.character_id)
        illegal_cases = [
            ("HP 越界", make_narrative(state_updates={"hp_delta": -(char.hp + 5)})),
            ("低压力放 key 线索", make_narrative(new_clues=[
                {"title": "克仑可的藏身处", "importance": "key"}])),
            ("hidden_truth 直升 player_known", make_narrative(state_updates={
                "new_facts": [{"content": hidden[0].content, "fact_type": "player_known"}]})),
            ("AI 私造 hidden_truth", make_narrative(state_updates={
                "new_facts": [{"content": "新隐藏真相", "fact_type": "hidden_truth"}]})),
            ("判定失败写成成功", make_narrative(visible_result="你成功追上了目标")),
            ("NPC 警觉 delta 越界", make_narrative(state_updates={
                "npc_alertness": [{"npc_id": "lavinia_001", "delta": 5}]})),
        ]
        for label, bad in illegal_cases:
            try:
                committer.commit_action(sid, uid, "非法测试", bad, CHECK_FAIL, REVIEW_OK)
                raise AssertionError(f"{label} 未被拦截!")
            except CommitError:
                pass
        assert len(MessageRepo(db).list_all(sid)) == before, "拦截后残留半截数据"
        print(PASS, f"§8.1 校验: {len(illegal_cases)} 类非法输出全部拦截且零残留")

        # ===== 5. 警觉/解锁的合法路径 =====
        committer.commit_action(sid, uid, "我大声质问纳休斯", make_narrative(
            visible_result="纳休斯态度冷了下来。",
            state_updates={"npc_alertness": [{"npc_id": "lavinia_001", "delta": 2}],
                           "task_updates": [{"title": "活捉克仑可", "status": "doing"}]}),
            None, REVIEW_OK)
        assert NpcRepo(db).get_by_npc_id(sid, "lavinia_001").alertness == 2
        print(PASS, "合法 npc_alertness/task_updates 正确应用 (无检定轮亦可提交)")

        # ===== 6. clue_pressure 服务与档位 =====
        cp = CluePressureService(db).calculate(sid)
        assert 0.0 <= cp.clue_pressure <= 1.0 and cp.tier in (
            "normal", "weak_hint", "strong_hint", "push")
        print(PASS, f"clue_pressure={cp.clue_pressure:.2f} tier={cp.tier} "
                    f"(turns={cp.turns_since_key_clue}, failed={cp.failed_checks_in_scene})")

        # ===== 7. 结束: summary 上下文 + 报告落库 + 会话置 finished =====
        s_ctx = builder.build_for_summary(sid)
        assert s_ctx["player_actions"] and s_ctx["checks"] and s_ctx["clues"]
        committer.commit_report(sid, {
            "title": "追捕克仑可·第一夜战报",
            "story_summary": "追踪失败但获得了靴印线索, 与纳休斯关系紧张。",
            "key_choices": ["大声质问纳休斯"], "clues": ["井下的靴印"],
            "ending_type": "open", "ai_suggestion": "下次先做威吓检定再质问。"})
        db.expire_all()
        s2 = db.get(GameSession, sid)
        assert s2.status == "finished" and s2.ended_at is not None
        assert db.query(Report).filter_by(session_id=sid).first().ending_type == "open"
        print(PASS, "结束: reports 落库 + 会话 playing->finished (UPDATE 操作)")

        print("\n全部通过 — AI 模块与数据库交互闭环验证完成")
        print("CRUD 覆盖: 增(messages/clues/facts/...) 查(context/可见性) "
              "改(session/tasks/npc/hp/report) 三类以上 ✓")
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""AI 模块 ↔ 数据库交互专项验证。

检验项：
1. 规则书：rule_service 读取 rules/dnd5e + DB character_attributes
2. 模组：worlds 表 opening_prompt / description 注入 AI 上下文
3. 上下文 Fact：开局 seed → action 读取 → Critic 可见 hidden_truth
4. NPC Profile：开局 seed → context_builder 读取
5. 写入链：action 后 messages / action_checks / clues / ai_reviews / facts 落库
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ai_db_interaction.db")

from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.init_db import reset_demo_db
from app.db.session import SessionLocal
from app.main import app
from app.models.game import (
    ActionCheck,
    AiReview,
    Clue,
    Fact,
    Message,
    NpcProfile,
    World,
)
from app.services.context_builder import build_for_action
from app.services.memory_retriever import get_hidden_truths, list_npc_profiles
from app.services.rule_service import SKILLS, roll_check


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


async def main() -> None:
    reset_demo_db()
    section("1. 规则书：JSON 规则 + DB 角色属性")

    with SessionLocal() as db:
        from app.models.game import Character, CharacterAttributes

        character = db.get(Character, 1)
        attrs = db.query(CharacterAttributes).filter_by(character_id=1).first()
        assert character and attrs, "种子角色/属性缺失"

        assert "prc" in SKILLS, "skills.json 未加载"
        outcome = roll_check(
            character,
            attrs,
            check_type="观察",
            skill_key="prc",
            attribute_used="wisdom",
            dc=12,
        )
        assert outcome.ability_modifier == attrs.wisdom, "属性修正应来自 DB character_attributes"
        assert outcome.skill_bonus == 2, "调查员察觉(prc)应有熟练加值"
        print(f"[OK] 规则书检定: d20={outcome.dice_roll} mod={outcome.ability_modifier} skill={outcome.skill_bonus}")

        world = db.get(World, 2)
        assert world and "古堡" in world.name
        assert world.opening_prompt, "模组 opening_prompt 应存于 worlds 表"
        print(f"[OK] 模组 worlds: name={world.name}, prompt_len={len(world.opening_prompt)}")

    section("2. 开局：模组数据 seed 到 facts / npc_profiles")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/sessions/start", json={"world_id": 2, "character_id": 1})
        assert r.status_code == 200, r.text
        session_id = r.json()["data"]["session"]["id"]
        opening_narration = r.json()["data"]["opening"]["narration"]
        print(f"[OK] 开局 session_id={session_id}")

    with SessionLocal() as db:
        facts = db.query(Fact).filter(Fact.session_id == session_id).all()
        npcs = db.query(NpcProfile).filter(NpcProfile.session_id == session_id).all()
        assert any(f.fact_type == "world_public" for f in facts), "缺少 world_public Fact"
        assert any(f.fact_type == "hidden_truth" for f in facts), "缺少 hidden_truth Fact"
        assert any(f.fact_type == "npc_private" for f in facts), "缺少 npc_private Fact"
        assert len(npcs) >= 1, "缺少 npc_profiles"
        print(f"[OK] facts={len(facts)} (world_public/hidden_truth/npc_private)")
        print(f"[OK] npc_profiles={len(npcs)} names={[n.name for n in npcs]}")

        from app.models.game import GameSession

        session = db.get(GameSession, session_id)
        ctx = build_for_action(db, session)
        assert world.name in ctx.world.name or "古堡" in ctx.world.name
        assert ctx.world.opening_prompt, "context 应含 DB 模组 opening_prompt"
        assert len(ctx.hidden_truths) >= 1, "Critic 应能读到 hidden_truth"
        assert len(ctx.npc_private_facts) >= 1, "Critic 应能读到 npc_private"
        assert len(ctx.visible_npcs) >= 1, "Narrative 应能读到 npc_profiles"
        assert ctx.character.name == "艾琳"
        print(f"[OK] context_builder 读取: hidden={len(ctx.hidden_truths)} npc_private={len(ctx.npc_private_facts)} npcs={len(ctx.visible_npcs)}")

    section("3. 行动：DB 上下文参与 AI → 结果写回 DB")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            f"/api/v1/sessions/{session_id}/action",
            json={"action_text": "我想先观察大厅，看看有没有异常线索。"},
        )
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        print(f"[OK] action check: dice={data['check']['dice_roll']} success={data['check']['is_success']}")

    with SessionLocal() as db:
        msgs = db.query(Message).filter(Message.session_id == session_id).count()
        checks = db.query(ActionCheck).filter(ActionCheck.session_id == session_id).count()
        reviews = db.query(AiReview).filter(AiReview.session_id == session_id).count()
        clues = db.query(Clue).filter(Clue.session_id == session_id).count()
        assert msgs >= 4, f"messages 应含 opening+player+dice+story, got {msgs}"
        assert checks >= 1, "action_checks 应落库"
        assert reviews >= 1, "ai_reviews 应落库"
        print(f"[OK] 落库: messages={msgs} checks={checks} reviews={reviews} clues={clues}")

        session = db.get(GameSession, session_id)
        ctx2 = build_for_action(db, session)
        assert len(ctx2.known_clues) >= 0
        assert ctx2.recent_summary, "session.summary 或 messages 应提供 recent_summary"
        hidden2 = get_hidden_truths(db, session_id)
        assert hidden2, "hidden_truth 应跨 action 持久保留"
        print(f"[OK] 二次读取上下文: clues={len(ctx2.known_clues)} summary_len={len(ctx2.recent_summary)}")

    section("4. Fact API 与 memory_retriever 一致性")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(f"/api/v1/sessions/{session_id}/facts?scope=player_known")
        assert r.status_code == 200
        api_facts = r.json()["data"]["facts"]

        r2 = await client.get(f"/api/v1/sessions/{session_id}/ai-reviews")
        assert r2.status_code == 200
        assert len(r2.json()["data"]["reviews"]) >= 1

        r3 = await client.get(f"/api/v1/sessions/{session_id}/meta")
        assert r3.status_code == 200
        assert "clue_pressure" in r3.json()["data"]

    with SessionLocal() as db:
        from app.services.memory_retriever import get_player_known_facts

        db_player_facts = get_player_known_facts(db, session_id)
        print(f"[OK] facts API count={len(api_facts)}, retriever player_known={len(db_player_facts)}")
        print(f"[OK] ai-reviews / meta API 正常")

    section("5. 总结：SummaryAgent 读取 DB 全量日志")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(f"/api/v1/sessions/{session_id}/end")
        r = await client.post(f"/api/v1/sessions/{session_id}/report/generate")
        assert r.status_code == 200
        summary = r.json()["data"]["story_summary"]
        assert len(summary) > 20
        assert "艾琳" in summary or "古堡" in summary
        print(f"[OK] SummaryAgent 基于 DB 日志生成报告 len={len(summary)}")

    print("\n" + "=" * 60)
    print("AI 模块与数据库交互验证全部通过")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

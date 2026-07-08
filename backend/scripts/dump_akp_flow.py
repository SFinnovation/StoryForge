# -*- coding: utf-8 -*-
"""采集 AKP 全流程的 agent 输入/输出 + AKP 证据包内容，落盘为 JSON（供可视化核验）。

用法（PowerShell）：
    $env:LLM_API_KEY="sk-..."; python backend/scripts/dump_akp_flow.py

产物：data/akp_flow_dump.json
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_akp_dump.db")
os.environ["AKP_ENABLED"] = "true"
os.environ.setdefault("AKP_BUNDLE_PRESET", "quick")

if not os.environ.get("LLM_API_KEY"):
    print("[ERROR] 需要环境变量 LLM_API_KEY。")
    raise SystemExit(1)

from backend.app.ai.schemas import ActionParseInput
from backend.app.ai.services import akp_client
from backend.app.ai.services.llm_client import close_llm_client
from backend.app.core.config import settings
from backend.app.db.database import SessionLocal
from backend.app.db.init_db import init_db
from backend.app.models.models import (
    AdventureModule,
    Character,
    Fact,
    GameSession,
    NpcProfile,
    RulebookPack,
    World,
)
from backend.app.services import action_service
from backend.app.services.ai_service import get_ai_service
from backend.app.services.content_ingestion_service import (
    MODULE_QUESTION_SET,
    RULEBOOK_QUESTION_SET,
    ingest_module_from_docx,
    ingest_rulebook_from_docx,
)
from backend.app.services.context_builder import build_for_action, build_for_opening, build_for_summary
from backend.app.services.state_committer import commit_opening
from backend.app.services.world_seed import seed_session_world_data

PHB = PROJECT_ROOT / "packs" / "rulebook_pack" / "5eDnD_玩家手册PHB_中译v1.6版_可复制文本.docx"
KRENKO = PROJECT_ROOT / "packs" / "mods_pack" / "追捕克仑可_Krenkos_Way_可复制文本 (1).docx"

WORLD_ID = 1
USER_ID = 1
OUT = PROJECT_ROOT / "data" / "akp_flow_dump.json"


def _capture_bundles(pack_dir: str, questions: list[str], prefix: str) -> list[dict]:
    """对已建包逐题检索，记录喂给提取 agent 的真实证据包内容。"""
    p = Path(pack_dir)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    out: list[dict] = []
    for i, q in enumerate(questions):
        try:
            b = akp_client.research(p, q, run_id=f"{prefix}{i + 1}")
        except akp_client.AkpError as exc:
            out.append({"question": q, "error": str(exc)})
            continue
        refs = [e.reference_path for e in b.evidence if e.reference_path]
        out.append({
            "question": q,
            "hits": b.hits,
            "verify_ok": b.verify_ok,
            "references": sorted(set(refs)),
            "bundle_md": b.bundle_md,
        })
    return out


def _seed_world() -> None:
    init_db(drop_first=True)
    with SessionLocal() as db:
        db.add(World(
            id=WORLD_ID, name="追捕克仑可（AKP 核验）", type="fantasy",
            description="AKP 核验世界", opening_prompt="待模组导入覆盖",
            rule_style="lite_dnd", difficulty="normal", is_enabled=1, created_by=1,
        ))
        db.add(Character(
            id=1, user_id=USER_ID, name="凯尔·维恩", race_id="human",
            class_id="赏金侦探", background_id="detective",
            motivation="追捕越狱的鬼怪黑帮头目克仑可，并查明其幕后雇主。",
            level=1, hp=9, max_hp=9,
            strength=13, dexterity=15, constitution=12,
            intelligence=14, wisdom=10, charisma=8,
            skills_json='{"per": {"proficient": true}, "inv": {"proficient": true}}',
            saving_throws_json='["dexterity", "intelligence"]',
            inventory_json="[]",
        ))
        db.commit()


async def main() -> int:
    if not (PHB.exists() and KRENKO.exists()):
        print("[ERROR] 缺少 docx。")
        return 2

    _seed_world()
    ai = get_ai_service()
    dump: dict = {
        "meta": {
            "model": settings.LLM_MODEL,
            "api_base": settings.LLM_API_BASE,
            "akp_bundle_preset": settings.AKP_BUNDLE_PRESET,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rulebook_file": PHB.name,
            "module_file": KRENKO.name,
        },
        "akp": {},
        "agents": {},
    }

    with SessionLocal() as db:
        # ---------- 1. 提取 agent（规则书 / 模组）----------
        rb_result, pack_id = await ingest_rulebook_from_docx(
            db, PHB, world_id=WORLD_ID, focus="lite_dnd"
        )
        mod_result, module_id = await ingest_module_from_docx(
            db, KRENKO, world_id=WORLD_ID, module_title="追捕克仑可"
        )
        rb_row = db.get(RulebookPack, pack_id)
        mod_row = db.get(AdventureModule, module_id)
        rb_dir = rb_row.knowledge_pack_dir
        mod_dir = mod_row.knowledge_pack_dir

        dump["agents"]["rulebook_extractor"] = {
            "input": {
                "source_name": PHB.name,
                "focus": "lite_dnd",
                "mode": "AKP 证据包模式（evidence_bundles）",
            },
            "output": rb_result.output.model_dump(),
            "tokens_used": rb_result.tokens_used,
            "latency_ms": rb_result.latency_ms,
        }
        dump["agents"]["module_extractor"] = {
            "input": {
                "source_name": KRENKO.name,
                "module_title": "追捕克仑可",
                "mode": "AKP 证据包模式（evidence_bundles）",
            },
            "output": mod_result.output.model_dump(),
            "tokens_used": mod_result.tokens_used,
            "latency_ms": mod_result.latency_ms,
        }

        # ---------- 2. AKP 证据包内容（喂给提取 agent 的真实材料）----------
        print("采集 AKP 证据包…")
        dump["akp"]["rulebook_pack"] = {
            "pack_dir": rb_dir,
            "bundles": _capture_bundles(rb_dir, RULEBOOK_QUESTION_SET, "rb_q"),
        }
        dump["akp"]["module_pack"] = {
            "pack_dir": mod_dir,
            "bundles": _capture_bundles(mod_dir, MODULE_QUESTION_SET, "mod_q"),
        }

        # ---------- 3. OpeningAgent ----------
        world = db.get(World, WORLD_ID)
        character = db.get(Character, 1)
        session = GameSession(
            user_id=USER_ID, world_id=WORLD_ID, character_id=1,
            title=world.name, status="playing", started_at=datetime.utcnow(),
        )
        db.add(session)
        db.flush()

        opening_input = build_for_opening(db, world, character)
        opening_result = await ai.generate_opening(opening_input)
        opening = opening_result.output
        commit_opening(
            db, session,
            narration=opening.display_text, scene_title=opening.scene_title,
            main_task=opening.main_task,
            tokens_used=opening_result.tokens_used, latency_ms=opening_result.latency_ms,
        )
        seed_session_world_data(db, session.id, world, opening)
        db.commit()
        session_id = session.id

        facts = db.query(Fact).filter(Fact.session_id == session_id).all()
        npcs = db.query(NpcProfile).filter(NpcProfile.session_id == session_id).all()
        by_type: dict[str, list[dict]] = {}
        for f in facts:
            by_type.setdefault(f.fact_type, []).append({
                "content": f.content, "importance": f.importance,
                "status": f.status, "related_scene": f.related_scene,
            })

        dump["agents"]["opening"] = {
            "input": opening_input.model_dump(),
            "output": opening.model_dump(),
            "tokens_used": opening_result.tokens_used,
            "latency_ms": opening_result.latency_ms,
            "seeded_facts_by_type": by_type,
            "seeded_npcs": [{
                "npc_id": n.npc_id, "name": n.name, "personality": n.personality,
                "knowledge_scope": json.loads(n.knowledge_scope_json or "[]"),
                "forbidden_knowledge": json.loads(n.forbidden_knowledge_json or "[]"),
                "related_scene": n.related_scene,
            } for n in npcs],
        }

        # ---------- 4. ActionParser + Narrative + Critic ----------
        actions = [
            "我仔细观察周围环境，留意任何与克仑可行踪相关的可疑线索。",
            "我压低声音向附近的线人打听克仑可最近的落脚点。",
        ]
        dump["agents"]["action_parser"] = []
        dump["agents"]["narrative"] = []
        for text in actions:
            ctx = build_for_action(db, session)
            parse_in = ActionParseInput(
                player_action=text, current_scene=ctx.current_scene,
                character=ctx.character, recent_summary=ctx.recent_summary,
            )
            parse_out = await ai.parse_action(parse_in)
            dump["agents"]["action_parser"].append({
                "input": parse_in.model_dump(),
                "output": parse_out.output.model_dump(),
                "tokens_used": parse_out.tokens_used,
                "latency_ms": parse_out.latency_ms,
            })

            narrative_ctx = {
                "current_scene": ctx.current_scene,
                "clue_pressure": ctx.clue_pressure,
                "known_clues": ctx.known_clues,
                "public_world_facts": ctx.public_world_facts,
                "visible_npcs": ctx.visible_npcs,
                "hidden_truths_count": len(ctx.hidden_truths),
                "npc_private_facts_count": len(ctx.npc_private_facts),
                "story_summary": ctx.story_summary,
            }
            result = await action_service.handle_action(db, session_id, USER_ID, text)
            data = result.model_dump()
            dump["agents"]["narrative"].append({
                "player_action": text,
                "narrative_input_context": narrative_ctx,
                "check": data["check"],
                "story": data["story"],
                "ai_review": data["ai_review"],
                "meta": data["meta"],
            })

        # ---------- 5. SummaryAgent ----------
        session = db.get(GameSession, session_id)
        summary_input = build_for_summary(db, session)
        summary_result = await ai.generate_summary(summary_input)
        dump["agents"]["summary"] = {
            "input": summary_input.model_dump(),
            "output": summary_result.output.model_dump(),
            "tokens_used": summary_result.tokens_used,
            "latency_ms": summary_result.latency_ms,
        }

    await close_llm_client()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 已写入 {OUT} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

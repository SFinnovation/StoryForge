"""内容导入编排 — docx →（可选 AKP 建包/检索）→ Agent 提取 → 数据库。"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.ai.schemas.agent_result import AgentResult
from backend.app.ai.schemas.module_extract import ModuleExtractionInput, ModuleExtractionOutput
from backend.app.ai.schemas.rulebook_extract import RulebookExtractionInput, RulebookExtractionOutput
from backend.app.ai.services import akp_client
from backend.app.ai.services.docx_extractor import extract_text_from_docx
from backend.app.services.ai_service import get_ai_service
from backend.app.services.content_pack_repository import (
    get_adventure_module,
    get_rulebook_pack,
    link_module_to_world,
    link_rulebook_to_world,
    save_adventure_module,
    save_rulebook_pack,
)

logger = logging.getLogger(__name__)

# 模式 A 提问清单（见 docs/akp-integration-plan.md §4）
RULEBOOK_QUESTION_SET: list[str] = [
    "属性检定如何计算？",
    "优势与劣势规则是什么？",
    "短休与长休如何恢复？",
    "死亡豁免规则是什么？",
    "先攻与战斗轮如何进行？",
    "技能与熟练加值如何运作？",
    "世界观背景与基调是什么？",
]

MODULE_QUESTION_SET: list[str] = [
    "故事主线与目标是什么？",
    "有哪些关键场景与出口？",
    "起始场景在哪里？",
    "关键隐藏真相有哪些？",
    "主要 NPC 及其秘密是什么？",
    "玩家可能已知的线索有哪些？",
]


def _build_evidence_bundles(
    file_path: Path, question_set: list[str], *, skill_name: str
) -> tuple[list[str], str | None]:
    """启用 AKP 时：建包 + 逐题检索，返回 (bundle_md 列表, pack 目录)。

    任何失败都吞掉并回退（返回空列表 / None），保证不破坏现有纯 LLM 路径。
    """
    if not akp_client.is_enabled():
        return [], None
    try:
        pack_dir = akp_client.build_pack([file_path], skill_name, title=file_path.stem)
    except akp_client.AkpError as exc:
        logger.warning("AKP 建包失败，回退纯 LLM 路径: %s", exc)
        return [], None

    bundles: list[str] = []
    for idx, question in enumerate(question_set):
        try:
            bundle = akp_client.research(pack_dir, question, run_id=f"q{idx + 1}")
        except akp_client.AkpError as exc:
            logger.warning("AKP 检索失败（跳过该问题）: %s (%s)", question, exc)
            continue
        if bundle.verify_ok:
            bundles.append(bundle.bundle_md)
    return bundles, str(pack_dir)


async def ingest_rulebook_from_docx(
    db: Session,
    file_path: str | Path,
    *,
    world_id: int | None = None,
    focus: str = "lite_dnd",
) -> tuple[AgentResult[RulebookExtractionOutput], int]:
    path = Path(file_path)
    raw_text = extract_text_from_docx(path)

    bundles, pack_dir = _build_evidence_bundles(
        path, RULEBOOK_QUESTION_SET, skill_name=f"rulebook-{path.stem}"
    )

    ai = get_ai_service()
    result = await ai.extract_rulebook(
        RulebookExtractionInput(
            source_name=path.name,
            raw_text=raw_text,
            focus=focus,
            evidence_bundles=bundles,
        )
    )
    pack = save_rulebook_pack(
        db, result.output, source_filename=path.name, knowledge_pack_dir=pack_dir
    )
    if world_id is not None:
        link_rulebook_to_world(db, world_id, pack.id)
    db.commit()
    return result, pack.id


async def ingest_module_from_docx(
    db: Session,
    file_path: str | Path,
    *,
    world_id: int | None = None,
    module_title: str = "",
) -> tuple[AgentResult[ModuleExtractionOutput], int]:
    path = Path(file_path)
    raw_text = extract_text_from_docx(path)

    bundles, pack_dir = _build_evidence_bundles(
        path, MODULE_QUESTION_SET, skill_name=f"module-{path.stem}"
    )

    ai = get_ai_service()
    result = await ai.extract_module(
        ModuleExtractionInput(
            source_name=path.name,
            raw_text=raw_text,
            module_title=module_title or path.stem,
            evidence_bundles=bundles,
        )
    )
    module = save_adventure_module(
        db, result.output, source_filename=path.name, knowledge_pack_dir=pack_dir
    )
    if world_id is not None:
        link_module_to_world(db, world_id, module.id)
    db.commit()
    return result, module.id


def load_world_content_context(db: Session, world) -> dict:
    """聚合世界观关联的规则书包与模组包，供 context_builder 使用。"""
    ctx: dict = {
        "rulebook": None,
        "module": None,
        "public_world_facts": [],
        "hidden_truths": [],
        "npc_private_facts": [],
        "scenes": [],
        "story_summary": "",
        "current_scene": None,
        "seed_npcs": [],
        "visible_npcs": [],
        "player_known_clues": [],
    }
    if world.rulebook_pack_id:
        rb = get_rulebook_pack(db, world.rulebook_pack_id)
        if rb:
            ctx["rulebook"] = rb
            ctx["public_world_facts"].extend([f.content for f in rb.public_world_facts])
    if world.adventure_module_id:
        mod = get_adventure_module(db, world.adventure_module_id)
        if mod:
            ctx["module"] = mod
            ctx["scenes"] = [s.model_dump() for s in mod.scenes]
            ctx["story_summary"] = mod.story_summary
            ctx["current_scene"] = mod.current_scene
            ctx["hidden_truths"].extend(mod.hidden_truths)
            ctx["public_world_facts"].extend(mod.public_world_facts)
            ctx["player_known_clues"].extend(mod.player_known_clues)
            ctx["npc_private_facts"].extend([f.content for f in mod.npc_private_facts])
            ctx["seed_npcs"] = [n.model_dump() for n in mod.seed_npcs]
            ctx["visible_npcs"] = [n.model_dump() for n in mod.visible_npcs]
    return ctx

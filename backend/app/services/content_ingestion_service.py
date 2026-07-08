"""内容导入编排 — docx → Agent 提取 → 数据库。"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.ai.schemas.agent_result import AgentResult
from backend.app.ai.schemas.module_extract import ModuleExtractionInput, ModuleExtractionOutput
from backend.app.ai.schemas.rulebook_extract import RulebookExtractionInput, RulebookExtractionOutput
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


async def ingest_rulebook_from_docx(
    db: Session,
    file_path: str | Path,
    *,
    world_id: int | None = None,
    focus: str = "lite_dnd",
) -> tuple[AgentResult[RulebookExtractionOutput], int]:
    path = Path(file_path)
    raw_text = extract_text_from_docx(path)
    ai = get_ai_service()
    result = await ai.extract_rulebook(
        RulebookExtractionInput(
            source_name=path.name,
            raw_text=raw_text,
            focus=focus,
        )
    )
    pack = save_rulebook_pack(db, result.output, source_filename=path.name)
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
    ai = get_ai_service()
    result = await ai.extract_module(
        ModuleExtractionInput(
            source_name=path.name,
            raw_text=raw_text,
            module_title=module_title or path.stem,
        )
    )
    module = save_adventure_module(db, result.output, source_filename=path.name)
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

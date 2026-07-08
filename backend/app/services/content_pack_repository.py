"""内容包持久化 — 规则书/模组提取结果落库与读取。"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.ai.schemas.module_extract import ModuleExtractionOutput
from backend.app.ai.schemas.rulebook_extract import RulebookExtractionOutput
from backend.app.models.models import AdventureModule, RulebookPack, World


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def save_rulebook_pack(
    db: Session,
    output: RulebookExtractionOutput,
    *,
    source_filename: str | None = None,
) -> RulebookPack:
    pack = RulebookPack(
        title=output.title,
        source_filename=source_filename,
        world_setting=output.world_setting,
        world_style=output.world_style,
        public_world_facts_json=json.dumps(
            [f.model_dump() for f in output.public_world_facts], ensure_ascii=False
        ),
        core_rules_summary=output.core_rules_summary,
        extraction_notes=output.extraction_notes,
        status="active",
        created_at=_now(),
    )
    db.add(pack)
    db.flush()
    return pack


def save_adventure_module(
    db: Session,
    output: ModuleExtractionOutput,
    *,
    source_filename: str | None = None,
) -> AdventureModule:
    module = AdventureModule(
        title=output.title,
        source_filename=source_filename,
        story_summary=output.story_summary,
        opening_prompt=output.opening_prompt,
        scenes_json=json.dumps([s.model_dump() for s in output.scenes], ensure_ascii=False),
        current_scene=output.current_scene,
        hidden_truths_json=json.dumps(output.hidden_truths, ensure_ascii=False),
        world_facts_json=json.dumps(output.world_facts, ensure_ascii=False),
        public_world_facts_json=json.dumps(output.public_world_facts, ensure_ascii=False),
        player_known_clues_json=json.dumps(output.player_known_clues, ensure_ascii=False),
        npc_private_facts_json=json.dumps(
            [f.model_dump() for f in output.npc_private_facts], ensure_ascii=False
        ),
        visible_npcs_json=json.dumps([n.model_dump() for n in output.visible_npcs], ensure_ascii=False),
        seed_npcs_json=json.dumps([n.model_dump() for n in output.seed_npcs], ensure_ascii=False),
        extraction_notes=output.extraction_notes,
        status="active",
        created_at=_now(),
    )
    db.add(module)
    db.flush()
    return module


def link_rulebook_to_world(db: Session, world_id: int, pack_id: int) -> World:
    world = db.get(World, world_id)
    if world is None:
        raise ValueError(f"world {world_id} not found")
    world.rulebook_pack_id = pack_id
    pack = db.get(RulebookPack, pack_id)
    if pack:
        world.description = pack.world_setting[:2000]
        world.rule_style = pack.world_style[:500]
        if pack.core_rules_summary:
            world.opening_prompt = (
                f"{pack.world_setting[:500]}\n\n规则摘要：{pack.core_rules_summary[:800]}"
            )
    return world


def link_module_to_world(db: Session, world_id: int, module_id: int) -> World:
    world = db.get(World, world_id)
    if world is None:
        raise ValueError(f"world {world_id} not found")
    module = db.get(AdventureModule, module_id)
    if module is None:
        raise ValueError(f"module {module_id} not found")
    world.adventure_module_id = module_id
    world.description = module.story_summary[:2000]
    world.opening_prompt = module.opening_prompt
    world.type = "fantasy"
    return world


def get_rulebook_pack(db: Session, pack_id: int) -> RulebookExtractionOutput | None:
    pack = db.get(RulebookPack, pack_id)
    if pack is None:
        return None
    from backend.app.ai.schemas.rulebook_extract import WorldFactItem

    facts = [WorldFactItem.model_validate(f) for f in json.loads(pack.public_world_facts_json or "[]")]
    return RulebookExtractionOutput(
        title=pack.title,
        world_setting=pack.world_setting,
        world_style=pack.world_style,
        public_world_facts=facts,
        core_rules_summary=pack.core_rules_summary or "",
        extraction_notes=pack.extraction_notes or "",
    )


def get_adventure_module(db: Session, module_id: int) -> ModuleExtractionOutput | None:
    row = db.get(AdventureModule, module_id)
    if row is None:
        return None
    from backend.app.ai.schemas.module_extract import ModuleFactItem, ModuleNpcSeed, ModuleScene
    from backend.app.ai.schemas.opening import OpeningNpc

    return ModuleExtractionOutput(
        title=row.title,
        story_summary=row.story_summary,
        opening_prompt=row.opening_prompt,
        scenes=[ModuleScene.model_validate(s) for s in json.loads(row.scenes_json or "[]")],
        current_scene=row.current_scene,
        hidden_truths=json.loads(row.hidden_truths_json or "[]"),
        world_facts=json.loads(row.world_facts_json or "[]"),
        public_world_facts=json.loads(row.public_world_facts_json or "[]"),
        player_known_clues=json.loads(row.player_known_clues_json or "[]"),
        npc_private_facts=[
            ModuleFactItem.model_validate(f) for f in json.loads(row.npc_private_facts_json or "[]")
        ],
        visible_npcs=[
            ModuleNpcSeed.model_validate(n) for n in json.loads(row.visible_npcs_json or "[]")
        ],
        seed_npcs=[OpeningNpc.model_validate(n) for n in json.loads(row.seed_npcs_json or "[]")],
        extraction_notes=row.extraction_notes or "",
    )

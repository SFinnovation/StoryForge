"""开局模组数据落库 — 从 AdventureModule 提取结果 seed 到 session。"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.schemas.module_extract import ModuleExtractionOutput
from app.ai.schemas.opening import OpeningOutput
from app.models.game import Fact, NpcProfile, World
from app.services.content_ingestion_service import load_world_content_context
from app.services.fact_repository import create_fact


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def seed_session_world_data(
    db: Session,
    session_id: int,
    world: World,
    opening: OpeningOutput,
) -> None:
    """开局后将模组/规则书提取内容写入 session 级 facts 与 npc_profiles。"""
    if db.query(Fact).filter(Fact.session_id == session_id).count() > 0:
        return

    pack_ctx = load_world_content_context(db, world)
    module: ModuleExtractionOutput | None = pack_ctx["module"]

    if module:
        _seed_from_module(db, session_id, module, opening.scene_title)
        return

    create_fact(
        db,
        session_id,
        content=world.description,
        fact_type="world_public",
        related_scene=opening.scene_title,
    )
    if world.type == "mystery":
        create_fact(
            db,
            session_id,
            content="钟摆停止是因为有人动过机关，钟摆背后存在暗格。",
            fact_type="hidden_truth",
            related_scene=opening.scene_title,
            importance="key",
            status="locked",
            visibility_json={"player": False, "dm": True},
        )


def _seed_from_module(
    db: Session,
    session_id: int,
    module: ModuleExtractionOutput,
    scene: str,
) -> None:
    for fact in module.public_world_facts:
        create_fact(
            db,
            session_id,
            content=fact,
            fact_type="world_public",
            related_scene=scene,
        )
    for fact in module.world_facts:
        create_fact(
            db,
            session_id,
            content=fact,
            fact_type="world_public",
            related_scene=scene,
        )
    for truth in module.hidden_truths:
        create_fact(
            db,
            session_id,
            content=truth,
            fact_type="hidden_truth",
            related_scene=scene,
            importance="key",
            status="locked",
            visibility_json={"player": False, "dm": True},
        )
    for clue in module.player_known_clues:
        create_fact(
            db,
            session_id,
            content=clue,
            fact_type="player_known",
            related_scene=scene,
        )
    for nf in module.npc_private_facts:
        create_fact(
            db,
            session_id,
            content=nf.content,
            fact_type="npc_private",
            related_scene=nf.related_scene or scene,
            importance=nf.importance,
            visibility_json={"player": False, "npcs": [nf.npc_id] if nf.npc_id else []},
        )

    for npc in module.visible_npcs:
        exists = (
            db.query(NpcProfile)
            .filter(NpcProfile.session_id == session_id, NpcProfile.npc_id == npc.npc_id)
            .first()
        )
        if exists:
            continue
        db.add(
            NpcProfile(
                session_id=session_id,
                npc_id=npc.npc_id,
                name=npc.name,
                personality=npc.personality or npc.description,
                knowledge_scope_json=json.dumps(npc.knowledge_scope, ensure_ascii=False),
                forbidden_json=json.dumps(npc.forbidden_knowledge, ensure_ascii=False),
                speaking_style=npc.speaking_style,
                alertness=0,
                current_scene=npc.current_scene or scene,
                created_at=_now(),
            )
        )

    for npc in module.seed_npcs:
        npc_id = npc.npc_id or f"npc_{npc.name}"
        exists = (
            db.query(NpcProfile)
            .filter(NpcProfile.session_id == session_id, NpcProfile.npc_id == npc_id)
            .first()
        )
        if exists:
            continue
        db.add(
            NpcProfile(
                session_id=session_id,
                npc_id=npc_id,
                name=npc.name,
                personality=npc.description,
                knowledge_scope_json="[]",
                forbidden_json="[]",
                alertness=0,
                current_scene=scene,
                created_at=_now(),
            )
        )

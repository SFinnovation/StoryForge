"""开局模组数据落库 — 世界观 Fact、NPC Profile、隐藏真相。"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.schemas.opening import OpeningOutput
from app.models.game import Fact, NpcProfile, World
from app.services.fact_repository import create_fact


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def seed_session_world_data(
    db: Session,
    session_id: int,
    world: World,
    opening: OpeningOutput,
) -> None:
    """开局后将模组（世界观）与 NPC 配置写入数据库，供后续 AI 上下文读取。"""
    existing = db.query(Fact).filter(Fact.session_id == session_id).count()
    if existing == 0:
        create_fact(
            db,
            session_id,
            content=world.description,
            fact_type="world_public",
            related_scene=opening.scene_title,
            importance="normal",
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
            create_fact(
                db,
                session_id,
                content="老管家知道午夜钟声与失踪学者有关，但不会轻易透露。",
                fact_type="npc_private",
                related_scene=opening.scene_title,
                importance="important",
                visibility_json={"player": False, "npcs": ["butler_001"]},
            )

    for npc in opening.npcs:
        npc_id = npc.npc_id or f"npc_{npc.name}"
        exists = (
            db.query(NpcProfile)
            .filter(NpcProfile.session_id == session_id, NpcProfile.npc_id == npc_id)
            .first()
        )
        if exists:
            continue
        knowledge = ["古堡日常", "大厅布局"]
        forbidden = ["最终 Boss 身份", "密室机关完整解法"]
        if npc_id == "butler_001":
            knowledge.append("午夜钟声")
        db.add(
            NpcProfile(
                session_id=session_id,
                npc_id=npc_id,
                name=npc.name,
                personality=npc.description or "谨慎",
                knowledge_scope_json=json.dumps(knowledge, ensure_ascii=False),
                forbidden_json=json.dumps(forbidden, ensure_ascii=False),
                speaking_style="礼貌、含糊",
                alertness=0,
                current_scene=opening.scene_title,
                created_at=_now(),
            )
        )

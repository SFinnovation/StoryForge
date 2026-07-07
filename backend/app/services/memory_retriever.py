"""记忆检索 — 从数据库读取 Fact / NPC 上下文供 AI 使用。"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.game import Fact, NpcProfile


def get_facts_by_types(db: Session, session_id: int, fact_types: list[str]) -> list[Fact]:
    return (
        db.query(Fact)
        .filter(Fact.session_id == session_id, Fact.fact_type.in_(fact_types))
        .order_by(Fact.id)
        .all()
    )


def get_player_known_facts(db: Session, session_id: int) -> list[str]:
    rows = get_facts_by_types(db, session_id, ["player_known", "world_public"])
    return [f.content for f in rows]


def get_hidden_truths(db: Session, session_id: int) -> list[str]:
    return [f.content for f in get_facts_by_types(db, session_id, ["hidden_truth"])]


def get_npc_private_facts(db: Session, session_id: int) -> list[str]:
    return [f.content for f in get_facts_by_types(db, session_id, ["npc_private"])]


def list_npc_profiles(db: Session, session_id: int) -> list[dict]:
    rows = db.query(NpcProfile).filter(NpcProfile.session_id == session_id).all()
    result: list[dict] = []
    for npc in rows:
        result.append(
            {
                "npc_id": npc.npc_id,
                "name": npc.name,
                "personality": npc.personality or "",
                "knowledge_scope": json.loads(npc.knowledge_scope_json or "[]"),
                "forbidden_knowledge": json.loads(npc.forbidden_json or "[]"),
                "speaking_style": npc.speaking_style or "",
                "alertness": npc.alertness,
                "current_scene": npc.current_scene,
            }
        )
    return result

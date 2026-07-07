"""Fact 写入 — State Committer 使用。"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.game import Fact, NpcProfile


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_fact(
    db: Session,
    session_id: int,
    *,
    content: str,
    fact_type: str,
    related_scene: str | None = None,
    importance: str = "normal",
    status: str = "active",
    visibility_json: dict | None = None,
) -> Fact:
    fact = Fact(
        session_id=session_id,
        content=content,
        fact_type=fact_type,
        visibility_json=json.dumps(visibility_json or {}, ensure_ascii=False),
        related_scene=related_scene,
        importance=importance,
        status=status,
        created_at=_now(),
    )
    db.add(fact)
    return fact


def commit_new_facts(
    db: Session,
    session_id: int,
    new_facts: list[dict],
    *,
    current_scene: str | None = None,
) -> list[Fact]:
    """写入 AI 返回的 new_facts，禁止 hidden_truth 直接升级为 player_known。"""
    hidden_contents = {
        f.content
        for f in db.query(Fact)
        .filter(Fact.session_id == session_id, Fact.fact_type == "hidden_truth")
        .all()
    }
    created: list[Fact] = []
    for item in new_facts:
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        fact_type = str(item.get("fact_type", "player_known"))
        if fact_type == "player_known" and content in hidden_contents:
            continue
        if fact_type not in {
            "world_public",
            "player_known",
            "hidden_truth",
            "npc_private",
            "session_fact",
            "temporary",
        }:
            fact_type = "player_known"
        existing = (
            db.query(Fact)
            .filter(Fact.session_id == session_id, Fact.content == content, Fact.fact_type == fact_type)
            .first()
        )
        if existing:
            continue
        fact = create_fact(
            db,
            session_id,
            content=content,
            fact_type=fact_type,
            related_scene=item.get("related_scene") or current_scene,
            importance=str(item.get("importance", "normal")),
            status=str(item.get("status", "active")),
            visibility_json=item.get("visibility_json"),
        )
        created.append(fact)
    return created


def update_npc_alertness(db: Session, session_id: int, deltas: list) -> None:
    for item in deltas:
        npc_id = getattr(item, "npc_id", None) or (item.get("npc_id") if isinstance(item, dict) else None)
        delta = getattr(item, "delta", 0) if not isinstance(item, dict) else item.get("delta", 0)
        if not npc_id:
            continue
        npc = (
            db.query(NpcProfile)
            .filter(NpcProfile.session_id == session_id, NpcProfile.npc_id == npc_id)
            .first()
        )
        if npc:
            npc.alertness = max(0, min(10, npc.alertness + int(delta)))

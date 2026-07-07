"""clue_pressure 计算 — 见 ai-module-design。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.game import ActionCheck, Clue, GameSession


def calculate(db: Session, session: GameSession) -> dict:
    total_clues = db.query(Clue).filter(Clue.session_id == session.id).count()
    key_clues = (
        db.query(Clue)
        .filter(Clue.session_id == session.id, Clue.importance == "key")
        .count()
    )
    failed = (
        db.query(ActionCheck)
        .filter(ActionCheck.session_id == session.id, ActionCheck.is_success == 0)
        .count()
    )
    total_checks = db.query(ActionCheck).filter(ActionCheck.session_id == session.id).count()

    base = min(1.0, total_clues * 0.08 + key_clues * 0.15)
    fail_ratio = (failed / total_checks) if total_checks else 0.0
    pressure = min(1.0, max(0.0, base + fail_ratio * 0.2))

    session.clue_pressure = pressure
    session.failed_checks_in_scene = failed
    if key_clues == 0:
        session.turns_since_key_clue = total_checks
    return {
        "clue_pressure": round(pressure, 2),
        "turns_since_key_clue": session.turns_since_key_clue,
        "failed_checks_in_scene": failed,
        "current_scene": session.current_scene or "",
    }

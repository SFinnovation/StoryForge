"""本局总结报告服务。"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.core.exceptions import StoryForgeError
from backend.app.models.models import Clue, GameSession, Report
from backend.app.schemas.session_schema import ReportDTO
from backend.app.services.ai_service import get_ai_service
from backend.app.services.context_builder import build_for_summary


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def generate_report(db: Session, session_id: int, user_id: int) -> ReportDTO:
    session = db.get(GameSession, session_id)
    if session is None:
        raise StoryForgeError("session not found", status_code=404)
    if session.user_id != user_id:
        raise StoryForgeError("forbidden", status_code=403)

    existing = db.query(Report).filter(Report.session_id == session_id).first()
    if existing:
        return _to_dto(existing)

    if session.status == "playing":
        session.status = "finished"
        session.ended_at = _now()

    ai = get_ai_service()
    summary_input = build_for_summary(db, session)
    result = await ai.generate_summary(summary_input)
    summary = result.output

    clues = [c.title for c in db.query(Clue).filter(Clue.session_id == session_id).all()]

    report = Report(
        session_id=session_id,
        title=summary.title,
        story_summary=summary.display_text,
        key_choices_json=json.dumps(summary.key_choices, ensure_ascii=False),
        clues_json=json.dumps(clues, ensure_ascii=False),
        ending_type=summary.ending_type,
        character_growth=summary.character_growth,
        ai_suggestion=summary.next_suggestion,
        created_at=_now(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _to_dto(report)


def get_report(db: Session, session_id: int, user_id: int) -> ReportDTO:
    session = db.get(GameSession, session_id)
    if session is None or session.user_id != user_id:
        raise StoryForgeError("session not found", status_code=404)
    report = db.query(Report).filter(Report.session_id == session_id).first()
    if report is None:
        raise StoryForgeError("report not found", status_code=404)
    return _to_dto(report)


def _to_dto(report: Report) -> ReportDTO:
    return ReportDTO(
        id=report.id,
        session_id=report.session_id,
        title=report.title,
        story_summary=report.story_summary,
        key_choices=json.loads(report.key_choices_json or "[]"),
        ending_type=report.ending_type,
        character_growth=report.character_growth or "",
        ai_suggestion=report.ai_suggestion or "",
    )

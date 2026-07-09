"""会话生命周期服务。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.core.exceptions import StoryForgeError
from backend.app.models.models import Character, GameSession, Message, World
from backend.app.schemas.session_schema import (
    MessageDTO,
    OpeningDTO,
    SessionDTO,
    SessionStartData,
    SessionStartRequest,
)
from backend.app.services.ai_service import get_ai_service
from backend.app.services.context_builder import build_for_opening
from backend.app.services.state_committer import commit_opening
from backend.app.services.world_seed import seed_session_world_data


def _now() -> datetime:
    return datetime.utcnow()


def _session_dto(session: GameSession) -> SessionDTO:
    return SessionDTO(
        id=session.id,
        status=session.status,
        title=session.title,
        current_scene=session.current_scene,
        current_task=session.current_task,
        world_id=session.world_id,
        character_id=session.character_id,
        difficulty=session.difficulty or "normal",
    )


def get_playing_session(db: Session, session_id: int, user_id: int) -> GameSession:
    session = db.get(GameSession, session_id)
    if session is None:
        raise StoryForgeError("session not found", status_code=404)
    if session.user_id != user_id:
        raise StoryForgeError("forbidden", status_code=403)
    if session.status != "playing":
        raise StoryForgeError("session is not in playing status", status_code=409)
    return session


async def start_session(db: Session, user_id: int, payload: SessionStartRequest) -> SessionStartData:
    existing = (
        db.query(GameSession)
        .filter(GameSession.user_id == user_id, GameSession.status == "playing")
        .first()
    )
    if existing:
        raise StoryForgeError("already has a playing session", status_code=409)

    world = db.get(World, payload.world_id)
    character = db.get(Character, payload.character_id)
    if world is None or not world.is_enabled:
        raise StoryForgeError("world not found", status_code=404)
    if character is None or character.user_id != user_id:
        raise StoryForgeError("character not found", status_code=404)

    session = GameSession(
        user_id=user_id,
        world_id=world.id,
        character_id=character.id,
        title=(payload.title or "").strip() or world.name,
        status="playing",
        difficulty=payload.difficulty,
        started_at=_now(),
    )
    db.add(session)
    db.flush()

    ai = get_ai_service()
    opening_input = build_for_opening(db, world, character)
    opening_result = await ai.generate_opening(opening_input)
    opening = opening_result.output

    msg = commit_opening(
        db,
        session,
        narration=opening.display_text,
        scene_title=opening.scene_title,
        main_task=opening.main_task,
        tokens_used=opening_result.tokens_used,
        latency_ms=opening_result.latency_ms,
    )
    seed_session_world_data(db, session.id, world, opening)
    db.commit()
    db.refresh(session)

    visible_npcs = [n.model_dump() for n in opening.npcs]
    return SessionStartData(
        session=_session_dto(session),
        opening=OpeningDTO(
            scene_title=opening.scene_title,
            narration=opening.narration,
            main_task=opening.main_task,
            npcs=visible_npcs,
            initial_clues=opening.initial_clues,
            visible_npcs=visible_npcs,
        ),
        messages=[
            MessageDTO(
                id=msg.id,
                content=msg.content,
                message_type=msg.message_type,
                sender_type=msg.sender_type,
                sender_name=msg.sender_name,
                created_at=msg.created_at,
            )
        ],
    )


def end_session(db: Session, session_id: int, user_id: int) -> SessionDTO:
    session = db.get(GameSession, session_id)
    if session is None:
        raise StoryForgeError("session not found", status_code=404)
    if session.user_id != user_id:
        raise StoryForgeError("forbidden", status_code=403)
    if session.status == "finished":
        return _session_dto(session)
    session.status = "finished"
    session.ended_at = _now()
    db.commit()
    db.refresh(session)
    return _session_dto(session)


def get_session_detail(db: Session, session_id: int, user_id: int) -> dict:
    session = db.get(GameSession, session_id)
    if session is None or session.user_id != user_id:
        raise StoryForgeError("session not found", status_code=404)
    messages = list_messages(db, session_id, user_id)
    return {
        "session": _session_dto(session).model_dump(),
        "messages": [m.model_dump() for m in messages],
    }


def list_messages(db: Session, session_id: int, user_id: int) -> list[MessageDTO]:
    session = db.get(GameSession, session_id)
    if session is None or session.user_id != user_id:
        raise StoryForgeError("session not found", status_code=404)
    rows = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.id)
        .all()
    )
    return [
        MessageDTO(
            id=m.id,
            content=m.content,
            message_type=m.message_type,
            sender_type=m.sender_type,
            sender_name=m.sender_name,
            created_at=m.created_at,
        )
        for m in rows
    ]

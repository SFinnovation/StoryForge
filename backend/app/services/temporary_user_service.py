from __future__ import annotations

import secrets
import time
from datetime import datetime

from sqlalchemy import delete, or_
from sqlalchemy.orm import Session

from backend.app.models.models import (
    ActionCheck,
    AiReview,
    Character,
    Clue,
    Fact,
    GameSession,
    Message,
    NpcProfile,
    Report,
    Room,
    RoomAction,
    RoomMember,
    RoomMessage,
    Task,
    User,
)
from backend.app.services.auth_service import hash_password


def create_guest_user(db: Session) -> User:
    for _ in range(10):
        suffix = secrets.token_hex(4)
        username = f"guest_{int(time.time())}_{suffix}"
        if db.query(User).filter(User.username == username).first() is not None:
            continue
        user = User(
            username=username,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            nickname=f"游客{suffix.upper()}",
            role="user",
            status="active",
            is_temporary=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    raise RuntimeError("failed to allocate guest account")


def _delete_sessions(db: Session, session_ids: set[int]) -> None:
    if not session_ids:
        return

    db.execute(delete(AiReview).where(AiReview.session_id.in_(session_ids)))
    db.execute(delete(ActionCheck).where(ActionCheck.session_id.in_(session_ids)))
    db.execute(delete(Clue).where(Clue.session_id.in_(session_ids)))
    db.execute(delete(Task).where(Task.session_id.in_(session_ids)))
    db.execute(delete(Report).where(Report.session_id.in_(session_ids)))
    db.execute(delete(Fact).where(Fact.session_id.in_(session_ids)))
    db.execute(delete(NpcProfile).where(NpcProfile.session_id.in_(session_ids)))
    db.execute(delete(Message).where(Message.session_id.in_(session_ids)))
    db.execute(delete(RoomMessage).where(RoomMessage.session_id.in_(session_ids)))
    db.execute(delete(RoomAction).where(RoomAction.session_id.in_(session_ids)))
    db.execute(delete(GameSession).where(GameSession.id.in_(session_ids)))


def cleanup_temporary_user(db: Session, user_id: int) -> bool:
    user = db.get(User, user_id)
    if user is None or not getattr(user, "is_temporary", 0):
        return False

    character_ids = {
        row[0]
        for row in db.query(Character.id).filter(Character.user_id == user_id).all()
    }
    session_filters = [
        GameSession.user_id == user_id,
        GameSession.host_user_id == user_id,
    ]
    if character_ids:
        session_filters.append(GameSession.character_id.in_(character_ids))
    session_ids = {
        row[0]
        for row in db.query(GameSession.id).filter(or_(*session_filters)).all()
    }

    owned_or_joined_rooms = (
        db.query(Room)
        .outerjoin(RoomMember, RoomMember.room_id == Room.id)
        .filter(or_(Room.owner_id == user_id, RoomMember.user_id == user_id))
        .all()
    )
    room_ids_to_delete: set[int] = set()

    for room in owned_or_joined_rooms:
        if room.current_session_id:
            session = db.get(GameSession, room.current_session_id)
            if session is not None and (
                session.user_id == user_id
                or session.host_user_id == user_id
                or session.character_id in character_ids
            ):
                session_ids.add(room.current_session_id)

        remaining_members = (
            db.query(RoomMember)
            .filter(RoomMember.room_id == room.id, RoomMember.user_id != user_id)
            .order_by(RoomMember.id.asc())
            .all()
        )
        if room.owner_id == user_id:
            if remaining_members:
                next_host = remaining_members[0]
                room.owner_id = next_host.user_id
                next_host.role = "host"
                if room.current_session_id in session_ids:
                    room.current_session_id = None
                    room.status = "waiting"
            else:
                room_ids_to_delete.add(room.id)

    db.execute(delete(RoomMember).where(RoomMember.user_id == user_id))
    db.query(RoomMessage).filter(RoomMessage.sender_user_id == user_id).update(
        {RoomMessage.sender_user_id: None},
        synchronize_session=False,
    )
    db.execute(delete(RoomAction).where(RoomAction.actor_user_id == user_id))

    if session_ids:
        for room in db.query(Room).filter(Room.current_session_id.in_(session_ids)).all():
            room.current_session_id = None
            if room.status == "playing":
                room.status = "waiting"
            room.updated_at = datetime.utcnow()

    _delete_sessions(db, session_ids)

    if room_ids_to_delete:
        db.execute(delete(RoomAction).where(RoomAction.room_id.in_(room_ids_to_delete)))
        db.execute(delete(RoomMessage).where(RoomMessage.room_id.in_(room_ids_to_delete)))
        db.execute(delete(RoomMember).where(RoomMember.room_id.in_(room_ids_to_delete)))
        db.execute(delete(Room).where(Room.id.in_(room_ids_to_delete)))

    db.execute(delete(Character).where(Character.user_id == user_id))
    db.delete(user)
    db.commit()
    return True

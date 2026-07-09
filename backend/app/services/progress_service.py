from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.models import Clue, GameSession, Message, Room, RoomAction, RoomMember, Task


def _clamp_percent(value: float) -> int:
    return max(0, min(100, int(round(value))))


def session_progress_stats(db: Session, session: GameSession | None) -> dict:
    if session is None:
        return {
            "progress_percent": 0,
            "action_count": 0,
            "clue_count": 0,
            "key_clue_count": 0,
            "task_done_count": 0,
            "task_total_count": 0,
        }

    action_count = (
        db.query(func.count(Message.id))
        .filter(Message.session_id == session.id, Message.message_type == "action")
        .scalar()
        or 0
    )
    clue_count = (
        db.query(func.count(Clue.id))
        .filter(Clue.session_id == session.id)
        .scalar()
        or 0
    )
    key_clue_count = (
        db.query(func.count(Clue.id))
        .filter(Clue.session_id == session.id, Clue.importance == "key")
        .scalar()
        or 0
    )
    task_total_count = (
        db.query(func.count(Task.id))
        .filter(Task.session_id == session.id)
        .scalar()
        or 0
    )
    task_done_count = (
        db.query(func.count(Task.id))
        .filter(Task.session_id == session.id, Task.status.in_(("done", "failed")))
        .scalar()
        or 0
    )
    task_doing_count = (
        db.query(func.count(Task.id))
        .filter(Task.session_id == session.id, Task.status == "doing")
        .scalar()
        or 0
    )

    if session.status in ("finished", "archived"):
        progress = 100
    else:
        task_progress = (
            ((task_done_count + task_doing_count * 0.5) / task_total_count) * 100
            if task_total_count
            else 0
        )
        clue_progress = min(90, key_clue_count * 18 + (clue_count - key_clue_count) * 7)
        action_progress = min(85, action_count * 10)
        pressure_progress = float(session.clue_pressure or 0) * 100
        started_progress = 8 if (action_count or clue_count or task_total_count) else 0
        progress = min(
            95,
            max(started_progress, task_progress, clue_progress, action_progress, pressure_progress),
        )

    return {
        "progress_percent": _clamp_percent(progress),
        "action_count": int(action_count),
        "clue_count": int(clue_count),
        "key_clue_count": int(key_clue_count),
        "task_done_count": int(task_done_count),
        "task_total_count": int(task_total_count),
    }


def room_progress_stats(db: Session, room: Room) -> dict:
    session = db.get(GameSession, room.current_session_id) if room.current_session_id else None
    stats = session_progress_stats(db, session)

    room_action_count = (
        db.query(func.count(RoomAction.id))
        .filter(RoomAction.room_id == room.id, RoomAction.status == "done")
        .scalar()
        or 0
    )
    if room_action_count > stats["action_count"]:
        stats["action_count"] = int(room_action_count)
        if session and session.status == "playing":
            stats["progress_percent"] = max(stats["progress_percent"], _clamp_percent(min(85, room_action_count * 10)))

    member_count = (
        db.query(func.count(RoomMember.id))
        .filter(RoomMember.room_id == room.id)
        .scalar()
        or 0
    )
    ready_count = (
        db.query(func.count(RoomMember.id))
        .filter(RoomMember.room_id == room.id, RoomMember.is_ready == 1)
        .scalar()
        or 0
    )
    team_sync = (member_count / room.max_players * 100) if room.max_players else 0

    return {
        **stats,
        "member_count": int(member_count),
        "ready_count": int(ready_count),
        "team_sync_percent": _clamp_percent(team_sync),
    }

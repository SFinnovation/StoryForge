from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_id, get_db_session
from backend.app.core.exceptions import StoryForgeError
from backend.app.schemas.action_schema import ActionRequest
from backend.app.schemas.api_response import success
from backend.app.schemas.session_schema import SessionStartRequest
from backend.app.services import action_service, report_service, session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start")
async def start_session(
    payload: SessionStartRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    data = await session_service.start_session(db, user_id, payload)
    return success(data.model_dump())


@router.get("")
def list_sessions(
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    from backend.app.models.models import AdventureModule, Character, GameSession, World
    from backend.app.services.progress_service import session_progress_stats

    rows = (
        db.query(GameSession, World, AdventureModule, Character)
        .join(World, World.id == GameSession.world_id)
        .join(Character, Character.id == GameSession.character_id)
        .outerjoin(AdventureModule, AdventureModule.id == World.adventure_module_id)
        .filter(GameSession.user_id == user_id)
        .order_by(GameSession.id.desc())
        .all()
    )
    items = []
    for session, world, module, character in rows:
        progress = session_progress_stats(db, session)
        items.append(
            {
                "id": session.id,
                "status": session.status,
                "title": session.title,
                "current_scene": session.current_scene,
                "current_task": session.current_task,
                "summary": session.summary,
                "difficulty": session.difficulty,
                "started_at": session.started_at,
                "ended_at": session.ended_at,
                "room_id": session.room_id,
                "mode": session.mode,
                "world_id": world.id,
                "world_name": world.name,
                "world_type": world.type,
                "character_id": character.id,
                "character_name": character.name,
                "character_level": character.level,
                "character_hp": character.hp,
                "character_max_hp": character.max_hp,
                "adventure_module_id": module.id if module else None,
                "adventure_module_title": module.title if module else None,
                "adventure_module_scene": module.current_scene if module else None,
                **progress,
            }
        )
    return success(items)


@router.delete("/{session_id}")
def delete_session_archive(
    session_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    from backend.app.models.models import (
        ActionCheck,
        AiReview,
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
    )

    session = db.get(GameSession, session_id)
    if session is None or session.user_id != user_id:
        raise StoryForgeError("session not found", status_code=404)

    room_id = session.room_id
    room_title = session.title
    room_to_delete = None

    try:
        if room_id is not None:
            room = db.get(Room, room_id)
            if room is not None and room.owner_id != user_id:
                raise StoryForgeError("only room owner can delete this archive", status_code=403)
            room_to_delete = room

            db.execute(delete(RoomAction).where(RoomAction.room_id == room_id))
            db.execute(delete(RoomMessage).where(RoomMessage.room_id == room_id))
            db.execute(delete(RoomMember).where(RoomMember.room_id == room_id))

        db.execute(delete(AiReview).where(AiReview.session_id == session_id))
        db.execute(delete(ActionCheck).where(ActionCheck.session_id == session_id))
        db.execute(delete(Clue).where(Clue.session_id == session_id))
        db.execute(delete(Task).where(Task.session_id == session_id))
        db.execute(delete(Report).where(Report.session_id == session_id))
        db.execute(delete(Fact).where(Fact.session_id == session_id))
        db.execute(delete(NpcProfile).where(NpcProfile.session_id == session_id))
        db.execute(delete(Message).where(Message.session_id == session_id))
        db.delete(session)
        db.flush()
        if room_to_delete is not None:
            db.delete(room_to_delete)
        db.commit()
    except StoryForgeError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    return success({
        "deleted": True,
        "session_id": session_id,
        "room_id": room_id,
        "title": room_title,
    })


@router.get("/{session_id}")
def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    return success(session_service.get_session_detail(db, session_id, user_id))


@router.get("/{session_id}/messages")
def get_messages(
    session_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    messages = session_service.list_messages(db, session_id, user_id)
    return success([m.model_dump() for m in messages])


@router.post("/{session_id}/action")
async def submit_action(
    session_id: int,
    payload: ActionRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    data = await action_service.handle_action(db, session_id, user_id, payload.action_text)
    return success(data.model_dump())


@router.post("/{session_id}/end")
def end_session(
    session_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    data = session_service.end_session(db, session_id, user_id)
    return success(data.model_dump())


@router.post("/{session_id}/report/generate")
async def generate_report(
    session_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    data = await report_service.generate_report(db, session_id, user_id)
    return success(data.model_dump())


@router.get("/{session_id}/report")
def get_report(
    session_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    data = report_service.get_report(db, session_id, user_id)
    return success(data.model_dump())


@router.get("/{session_id}/meta")
def get_session_meta(
    session_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    data = action_service.get_session_meta(db, session_id, user_id)
    return success(data.model_dump())


@router.get("/{session_id}/facts")
def get_facts(
    session_id: int,
    scope: str = Query(default="player_known"),
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    facts = action_service.list_facts(db, session_id, user_id, scope)
    return success({"facts": facts})


@router.get("/{session_id}/ai-reviews")
def get_ai_reviews(
    session_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    reviews = action_service.list_ai_reviews(db, session_id, user_id, limit)
    return success({"reviews": reviews})

from fastapi import APIRouter, Depends, Query
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
    from backend.app.models.models import GameSession

    rows = db.query(GameSession).filter(GameSession.user_id == user_id).order_by(GameSession.id.desc()).all()
    return success(
        [
            {
                "id": s.id,
                "status": s.status,
                "title": s.title,
                "current_scene": s.current_scene,
                "started_at": s.started_at,
            }
            for s in rows
        ]
    )


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

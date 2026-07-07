from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.services.export import export_service
from app.services.story import story_service

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/{story_id}/markdown", response_class=PlainTextResponse)
def export_markdown(story_id: int, db: Session = Depends(get_db_session)) -> str:
    if story_service.get_story(db, story_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return export_service.export_markdown(db, story_id)


@router.get("/{story_id}/pdf")
def export_pdf(story_id: int, db: Session = Depends(get_db_session)) -> Response:
    if story_service.get_story(db, story_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    content = export_service.export_pdf(db, story_id)
    return Response(content=content, media_type="application/pdf")

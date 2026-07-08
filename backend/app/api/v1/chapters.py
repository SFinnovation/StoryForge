from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db_session
from backend.app.schemas.chapter import ChapterCreate, ChapterResponse, ChapterUpdate
from backend.app.services.chapter import chapter_service

router = APIRouter(prefix="/chapters", tags=["chapters"])


@router.get("", response_model=list[ChapterResponse])
def list_chapters(story_id: int, db: Session = Depends(get_db_session)) -> list[ChapterResponse]:
    return chapter_service.list_chapters(db, story_id)


@router.post("", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
def create_chapter(
    payload: ChapterCreate,
    db: Session = Depends(get_db_session),
) -> ChapterResponse:
    return chapter_service.create_chapter(db, payload)


@router.get("/{chapter_id}", response_model=ChapterResponse)
def get_chapter(chapter_id: int, db: Session = Depends(get_db_session)) -> ChapterResponse:
    chapter = chapter_service.get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return chapter


@router.patch("/{chapter_id}", response_model=ChapterResponse)
def update_chapter(
    chapter_id: int,
    payload: ChapterUpdate,
    db: Session = Depends(get_db_session),
) -> ChapterResponse:
    chapter = chapter_service.get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return chapter_service.update_chapter(db, chapter, payload)


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(chapter_id: int, db: Session = Depends(get_db_session)) -> None:
    chapter = chapter_service.get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    chapter_service.delete_chapter(db, chapter)

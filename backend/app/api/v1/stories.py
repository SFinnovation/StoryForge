from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.story import StoryCreate, StoryResponse, StoryUpdate
from app.services.story import story_service

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("", response_model=list[StoryResponse])
def list_stories(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db_session),
) -> list[StoryResponse]:
    return story_service.list_stories(db, skip=skip, limit=limit)


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
def create_story(
    payload: StoryCreate,
    db: Session = Depends(get_db_session),
) -> StoryResponse:
    return story_service.create_story(db, payload)


@router.get("/{story_id}", response_model=StoryResponse)
def get_story(story_id: int, db: Session = Depends(get_db_session)) -> StoryResponse:
    story = story_service.get_story(db, story_id)
    if story is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return story


@router.patch("/{story_id}", response_model=StoryResponse)
def update_story(
    story_id: int,
    payload: StoryUpdate,
    db: Session = Depends(get_db_session),
) -> StoryResponse:
    story = story_service.get_story(db, story_id)
    if story is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return story_service.update_story(db, story, payload)


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(story_id: int, db: Session = Depends(get_db_session)) -> None:
    story = story_service.get_story(db, story_id)
    if story is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    story_service.delete_story(db, story)

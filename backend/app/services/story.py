from sqlalchemy.orm import Session

from backend.app.models.story import Story
from backend.app.schemas.story import StoryCreate, StoryUpdate


class StoryService:
    def list_stories(self, db: Session, *, skip: int = 0, limit: int = 20) -> list[Story]:
        return db.query(Story).offset(skip).limit(limit).all()

    def get_story(self, db: Session, story_id: int) -> Story | None:
        return db.query(Story).filter(Story.id == story_id).first()

    def create_story(self, db: Session, payload: StoryCreate) -> Story:
        story = Story(**payload.model_dump())
        db.add(story)
        db.commit()
        db.refresh(story)
        return story

    def update_story(self, db: Session, story: Story, payload: StoryUpdate) -> Story:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(story, field, value)
        db.commit()
        db.refresh(story)
        return story

    def delete_story(self, db: Session, story: Story) -> None:
        db.delete(story)
        db.commit()


story_service = StoryService()

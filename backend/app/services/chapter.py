from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.schemas.chapter import ChapterCreate, ChapterUpdate


class ChapterService:
    def list_chapters(self, db: Session, story_id: int) -> list[Chapter]:
        return db.query(Chapter).filter(Chapter.story_id == story_id).order_by(Chapter.order).all()

    def get_chapter(self, db: Session, chapter_id: int) -> Chapter | None:
        return db.query(Chapter).filter(Chapter.id == chapter_id).first()

    def create_chapter(self, db: Session, payload: ChapterCreate) -> Chapter:
        chapter = Chapter(**payload.model_dump())
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return chapter

    def update_chapter(self, db: Session, chapter: Chapter, payload: ChapterUpdate) -> Chapter:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(chapter, field, value)
        db.commit()
        db.refresh(chapter)
        return chapter

    def delete_chapter(self, db: Session, chapter: Chapter) -> None:
        db.delete(chapter)
        db.commit()


chapter_service = ChapterService()

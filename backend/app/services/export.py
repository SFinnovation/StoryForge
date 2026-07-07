from sqlalchemy.orm import Session

from app.models.story import Story


class ExportService:
    def export_markdown(self, db: Session, story_id: int) -> str:
        story = db.query(Story).filter(Story.id == story_id).first()
        if story is None:
            return ""
        return f"# {story.title}\n\n{story.description or ''}"

    def export_pdf(self, db: Session, story_id: int) -> bytes:
        # TODO: 实现 PDF 导出
        _ = db, story_id
        return b""


export_service = ExportService()

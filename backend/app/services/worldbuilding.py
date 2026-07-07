from sqlalchemy.orm import Session

from app.models.worldbuilding import WorldbuildingEntry
from app.schemas.worldbuilding import WorldbuildingEntryCreate, WorldbuildingEntryUpdate


class WorldbuildingService:
    def list_entries(self, db: Session, story_id: int) -> list[WorldbuildingEntry]:
        return db.query(WorldbuildingEntry).filter(WorldbuildingEntry.story_id == story_id).all()

    def get_entry(self, db: Session, entry_id: int) -> WorldbuildingEntry | None:
        return db.query(WorldbuildingEntry).filter(WorldbuildingEntry.id == entry_id).first()

    def create_entry(self, db: Session, payload: WorldbuildingEntryCreate) -> WorldbuildingEntry:
        entry = WorldbuildingEntry(**payload.model_dump())
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def update_entry(
        self,
        db: Session,
        entry: WorldbuildingEntry,
        payload: WorldbuildingEntryUpdate,
    ) -> WorldbuildingEntry:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)
        db.commit()
        db.refresh(entry)
        return entry

    def delete_entry(self, db: Session, entry: WorldbuildingEntry) -> None:
        db.delete(entry)
        db.commit()


worldbuilding_service = WorldbuildingService()

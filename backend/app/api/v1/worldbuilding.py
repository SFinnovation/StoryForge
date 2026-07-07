from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.worldbuilding import (
    WorldbuildingEntryCreate,
    WorldbuildingEntryResponse,
    WorldbuildingEntryUpdate,
)
from app.services.worldbuilding import worldbuilding_service

router = APIRouter(prefix="/worldbuilding", tags=["worldbuilding"])


@router.get("", response_model=list[WorldbuildingEntryResponse])
def list_entries(
    story_id: int,
    db: Session = Depends(get_db_session),
) -> list[WorldbuildingEntryResponse]:
    return worldbuilding_service.list_entries(db, story_id)


@router.post("", response_model=WorldbuildingEntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    payload: WorldbuildingEntryCreate,
    db: Session = Depends(get_db_session),
) -> WorldbuildingEntryResponse:
    return worldbuilding_service.create_entry(db, payload)


@router.get("/{entry_id}", response_model=WorldbuildingEntryResponse)
def get_entry(entry_id: int, db: Session = Depends(get_db_session)) -> WorldbuildingEntryResponse:
    entry = worldbuilding_service.get_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


@router.patch("/{entry_id}", response_model=WorldbuildingEntryResponse)
def update_entry(
    entry_id: int,
    payload: WorldbuildingEntryUpdate,
    db: Session = Depends(get_db_session),
) -> WorldbuildingEntryResponse:
    entry = worldbuilding_service.get_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return worldbuilding_service.update_entry(db, entry, payload)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, db: Session = Depends(get_db_session)) -> None:
    entry = worldbuilding_service.get_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    worldbuilding_service.delete_entry(db, entry)

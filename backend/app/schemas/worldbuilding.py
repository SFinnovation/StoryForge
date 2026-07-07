from pydantic import BaseModel, ConfigDict, Field


class WorldbuildingEntryBase(BaseModel):
    entry_type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    content: str | None = None


class WorldbuildingEntryCreate(WorldbuildingEntryBase):
    story_id: int


class WorldbuildingEntryUpdate(BaseModel):
    entry_type: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=255)
    content: str | None = None


class WorldbuildingEntryResponse(WorldbuildingEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    story_id: int

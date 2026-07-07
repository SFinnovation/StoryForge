from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StoryBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str | None = None
    status: str = "draft"


class StoryCreate(StoryBase):
    pass


class StoryUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    status: str | None = None


class StoryResponse(StoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

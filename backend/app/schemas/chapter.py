from pydantic import BaseModel, ConfigDict, Field


class ChapterBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str | None = None
    order: int = 0
    parent_id: int | None = None


class ChapterCreate(ChapterBase):
    story_id: int


class ChapterUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: str | None = None
    order: int | None = None
    parent_id: int | None = None


class ChapterResponse(ChapterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    story_id: int

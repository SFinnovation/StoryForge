from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    message: str


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    page: int
    page_size: int
    items: list

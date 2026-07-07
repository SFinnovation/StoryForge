from pydantic import BaseModel, Field


class CharacterCard(BaseModel):
    name: str
    profession: str = ""
    background: str = ""
    motivation: str = ""


class WorldContext(BaseModel):
    name: str = Field(..., description="世界观名称，如「古堡悬疑」")
    description: str = ""
    style: str = ""
    opening_prompt: str = ""

from pydantic import BaseModel, Field

from backend.app.ai.schemas.character import CharacterCard


class ActionParseInput(BaseModel):
    player_action: str
    current_scene: str = ""
    character: CharacterCard | None = None
    recent_summary: str = ""


class ActionParseOutput(BaseModel):
    action_type: str
    skill_key: str | None = None
    check_type: str
    attribute_used: str
    suggested_dc: int = Field(ge=5, le=30)
    needs_check: bool = True
    target: str | None = None
    intent: str = ""
    reason: str = ""

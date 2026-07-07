from pydantic import BaseModel, Field

from app.ai.schemas.character import CharacterCard, WorldContext
from app.ai.schemas.narrative import CheckResult


class SummaryInput(BaseModel):
    world: str | WorldContext
    character: CharacterCard
    player_actions: list[str] = Field(default_factory=list)
    check_results: list[CheckResult] = Field(default_factory=list)
    ai_narrations: list[str] = Field(default_factory=list)
    discovered_clues: list[str | dict] = Field(default_factory=list)
    task_status: list[dict] = Field(default_factory=list)
    session_summary: str = ""


class SummaryOutput(BaseModel):
    title: str
    story_summary: str
    key_choices: list[str] = Field(default_factory=list)
    ending_type: str = "open"
    character_growth: str = ""
    next_suggestion: str = ""

    @property
    def display_text(self) -> str:
        return self.story_summary.strip()

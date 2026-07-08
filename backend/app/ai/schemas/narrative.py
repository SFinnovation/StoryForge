from pydantic import BaseModel, Field

from backend.app.ai.schemas.character import CharacterCard, WorldContext
from backend.app.ai.schemas.critic import CriticOutput


class CheckResult(BaseModel):
    success: bool
    dice_roll: int | None = None
    final_value: int | None = None
    dc: int | None = None
    check_type: str | None = None
    attribute_used: str | None = None
    result_text: str | None = None


class NewClue(BaseModel):
    title: str
    content: str
    importance: str = "normal"
    visibility: str = "player_known"


class TaskUpdate(BaseModel):
    title: str
    status: str = "doing"


class NpcAlertnessDelta(BaseModel):
    npc_id: str
    delta: int = Field(default=0, ge=-3, le=3)


class StateUpdates(BaseModel):
    scene: str | None = None
    summary_delta: str = ""
    hp_delta: int = 0
    npc_alertness: list[NpcAlertnessDelta] = Field(default_factory=list)
    task_updates: list[TaskUpdate] = Field(default_factory=list)
    new_facts: list[dict] = Field(default_factory=list)


class NarrativeInput(BaseModel):
    """主叙事 Agent 输入 — 判定结果由后端传入，AI 不得修改。"""

    player_action: str
    check_result: CheckResult | None = None
    current_scene: str = ""
    known_clues: list[str | dict] = Field(default_factory=list)
    clue_pressure: float = Field(default=0.0, ge=0.0, le=1.0)
    world: str | WorldContext | None = None
    character: CharacterCard | None = None
    recent_summary: str = ""
    visible_npcs: list[dict] = Field(default_factory=list)
    public_world_facts: list[str] = Field(default_factory=list)
    scenes: list[dict] = Field(default_factory=list)
    story_summary: str = ""
    revision_instructions: list[str] = Field(default_factory=list)
    previous_narration: str | None = None


class NarrativeOutput(BaseModel):
    narration: str
    visible_result: str = ""
    new_clues: list[NewClue] = Field(default_factory=list)
    state_updates: StateUpdates = Field(default_factory=StateUpdates)
    next_options: list[str] = Field(default_factory=list)


class NarrativeWithReviewResult(BaseModel):
    """Narrative + Critic 审核结果 — 供后端 State Committer 使用。"""

    narrative: NarrativeOutput
    review: CriticOutput
    revision_count: int = 0
    used_fallback: bool = False
    tokens_used: int = 0
    latency_ms: int = 0

    @property
    def approved(self) -> bool:
        return self.review.approved

    @property
    def display_text(self) -> str:
        return self.narrative.narration.strip()

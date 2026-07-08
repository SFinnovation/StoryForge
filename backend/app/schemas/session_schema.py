from datetime import datetime

from pydantic import BaseModel, Field


class SessionStartRequest(BaseModel):
    world_id: int
    character_id: int


class MessageDTO(BaseModel):
    id: int
    content: str
    message_type: str
    sender_type: str = "player"
    sender_name: str | None = None
    created_at: datetime | str | None = None


class SessionDTO(BaseModel):
    id: int
    status: str
    title: str | None = None
    current_scene: str | None = None
    current_task: str | None = None
    world_id: int
    character_id: int


class OpeningDTO(BaseModel):
    scene_title: str
    narration: str
    main_task: str
    npcs: list[dict] = Field(default_factory=list)
    initial_clues: list[dict] = Field(default_factory=list)
    visible_npcs: list[dict] = Field(default_factory=list)


class SessionStartData(BaseModel):
    session: SessionDTO
    opening: OpeningDTO
    messages: list[MessageDTO] = Field(default_factory=list)


class CheckDTO(BaseModel):
    id: int | None = None
    check_type: str
    skill_key: str | None = None
    attribute_used: str
    dc: int
    dice_roll: int
    ability_modifier: int
    skill_bonus: int
    final_value: int
    is_success: bool
    result_text: str


class StoryDTO(BaseModel):
    message_id: int
    narration: str
    visible_result: str = ""
    new_clues: list[dict] = Field(default_factory=list)
    task_updates: list[dict] = Field(default_factory=list)
    next_options: list[str] = Field(default_factory=list)


class SessionMetaDTO(BaseModel):
    current_scene: str
    clue_pressure: float
    turns_since_key_clue: int = 0


class AiReviewDTO(BaseModel):
    approved: bool
    overall_score: int
    revision_count: int = 0
    used_fallback: bool = False
    scores: dict[str, int] = Field(default_factory=dict)


class ActionMetaDTO(BaseModel):
    tokens_used: int = 0
    latency_ms: int = 0


class ActionData(BaseModel):
    player_message: MessageDTO
    check: CheckDTO | None = None
    story: StoryDTO
    session_meta: SessionMetaDTO
    ai_review: AiReviewDTO
    meta: ActionMetaDTO


class ReportDTO(BaseModel):
    id: int
    session_id: int
    title: str | None = None
    story_summary: str
    key_choices: list[str] = Field(default_factory=list)
    ending_type: str = "open"
    character_growth: str = ""
    ai_suggestion: str = ""

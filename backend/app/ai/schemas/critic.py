from pydantic import BaseModel, Field, model_validator


class CriticScores(BaseModel):
    rule_consistency: int = Field(ge=0, le=100)
    world_consistency: int = Field(ge=0, le=100)
    context_continuity: int = Field(ge=0, le=100)
    character_alignment: int = Field(ge=0, le=100)
    npc_knowledge_boundary: int = Field(ge=0, le=100)
    clue_progression: int = Field(ge=0, le=100)


class CriticOutput(BaseModel):
    approved: bool
    overall_score: int = Field(ge=0, le=100)
    scores: CriticScores
    fatal_errors: list[str] = Field(default_factory=list)
    revision_instructions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_fatal_rejection(self) -> "CriticOutput":
        if self.fatal_errors:
            object.__setattr__(self, "approved", False)
        return self

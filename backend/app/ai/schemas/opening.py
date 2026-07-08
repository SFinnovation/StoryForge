from pydantic import BaseModel, Field

from app.ai.schemas.character import CharacterCard, WorldContext


class OpeningNpc(BaseModel):
    npc_id: str = ""
    name: str
    description: str = ""


class OpeningInput(BaseModel):
    """开局生成输入 — 后端传入世界观与角色卡。"""

    world: str | WorldContext
    character: CharacterCard
    public_world_facts: list[str] = Field(default_factory=list)
    seed_npcs: list[OpeningNpc] = Field(default_factory=list)

    def resolved_world(self) -> WorldContext:
        if isinstance(self.world, WorldContext):
            return self.world
        return WorldContext(name=self.world)


class OpeningOutput(BaseModel):
    scene_title: str
    narration: str
    main_task: str
    npcs: list[OpeningNpc] = Field(default_factory=list)
    initial_clues: list[dict] = Field(default_factory=list)
    initial_facts: list[dict] = Field(default_factory=list)

    @property
    def display_text(self) -> str:
        """面向前端的完整开局文本（含场景要点）。"""
        return self.narration.strip()

from pydantic import BaseModel, Field, field_validator

from backend.app.ai.schemas.character import CharacterCard, WorldContext


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

    @field_validator("initial_clues", "initial_facts", mode="before")
    @classmethod
    def _normalize_items(cls, value: object) -> list[dict]:
        """兼容 LLM 返回字符串数组：将字符串项规范化为 dict。"""
        if not isinstance(value, list):
            return []
        normalized: list[dict] = []
        for item in value:
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str) and item.strip():
                normalized.append({"content": item.strip()})
        return normalized

    @property
    def display_text(self) -> str:
        """面向前端的完整开局文本（含场景要点）。"""
        return self.narration.strip()

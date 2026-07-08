from pydantic import BaseModel, Field

from backend.app.ai.schemas.opening import OpeningNpc


class ModuleScene(BaseModel):
    scene_id: str
    title: str
    description: str = ""
    exits: list[str] = Field(default_factory=list)
    points_of_interest: list[str] = Field(default_factory=list)


class ModuleNpcSeed(BaseModel):
    npc_id: str
    name: str
    description: str = ""
    personality: str = ""
    knowledge_scope: list[str] = Field(default_factory=list)
    forbidden_knowledge: list[str] = Field(default_factory=list)
    speaking_style: str = ""
    current_scene: str = ""


class ModuleFactItem(BaseModel):
    content: str
    fact_type: str = Field(
        description="world_public | hidden_truth | npc_private | player_known"
    )
    related_scene: str = ""
    importance: str = "normal"
    npc_id: str | None = None


class ModuleExtractionInput(BaseModel):
    """冒险模组提取输入。"""

    source_name: str
    raw_text: str = Field(..., min_length=200)
    module_title: str = ""
    language: str = "zh"


class ModuleExtractionOutput(BaseModel):
    """模组标准化输出 — 落库后供开局/行动/审核 Agent 读取。"""

    title: str
    story_summary: str = Field(..., description="模组整体剧情摘要")
    opening_prompt: str = Field(..., description="供 OpeningAgent 使用的开局 system 上下文")
    scenes: list[ModuleScene] = Field(default_factory=list)
    current_scene: str = Field(..., description="推荐起始场景 scene_id 或标题")
    hidden_truths: list[str] = Field(default_factory=list)
    world_facts: list[str] = Field(default_factory=list)
    public_world_facts: list[str] = Field(default_factory=list)
    player_known_clues: list[str] = Field(default_factory=list)
    npc_private_facts: list[ModuleFactItem] = Field(default_factory=list)
    visible_npcs: list[ModuleNpcSeed] = Field(default_factory=list)
    seed_npcs: list[OpeningNpc] = Field(default_factory=list)
    extraction_notes: str = ""

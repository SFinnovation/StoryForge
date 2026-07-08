from pydantic import BaseModel, Field


class WorldFactItem(BaseModel):
    content: str
    importance: str = "normal"
    category: str = ""
    source_ref: str = Field(default="", description="AKP references/ 出处路径或 node_id（可选）")


class RulebookExtractionInput(BaseModel):
    """规则书提取输入。"""

    source_name: str = Field(..., description="来源文件名或标题")
    raw_text: str = Field(..., min_length=100, description="从 docx 提取的纯文本")
    focus: str = Field(
        default="lite_dnd",
        description="提取焦点：lite_dnd=跑团叙事所需轻量规则，full=完整规则摘要",
    )
    language: str = "zh"
    evidence_bundles: list[str] = Field(
        default_factory=list,
        description="AKP 检索产出的带出处证据包（bundle.md）；非空时优先据此提炼",
    )


class RulebookExtractionOutput(BaseModel):
    """规则书标准化输出 — 落库后供所有 Agent 读取。"""

    title: str
    world_setting: str = Field(..., description="世界观/战役设定摘要，供 Agent 理解世界基调")
    world_style: str = Field(..., description="叙事风格指引，如「奇幻冒险·英雄主义·中等难度」")
    public_world_facts: list[WorldFactItem] = Field(default_factory=list)
    core_rules_summary: str = Field(default="", description="检定/属性/战斗等核心规则压缩摘要")
    extraction_notes: str = Field(default="", description="提取过程备注或遗漏说明")

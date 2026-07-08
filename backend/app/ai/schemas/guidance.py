# -*- coding: utf-8 -*-
"""GuidanceAgent 输入/输出 (multiplayer-realtime-design §6.5)"""
from pydantic import BaseModel, Field

from backend.app.ai.schemas.character import CharacterCard, WorldContext


class GuidanceInput(BaseModel):
    question: str
    world: WorldContext
    character: CharacterCard
    current_scene: str = ""
    current_task: str | None = None
    known_clues: list[str] = Field(default_factory=list)
    public_world_facts: list[str] = Field(default_factory=list)
    visible_npcs: list[dict] = Field(default_factory=list)
    active_tasks: list[str] = Field(default_factory=list)
    recent_summary: str = ""


class GuidanceOutput(BaseModel):
    answer: str
    suggested_options: list[str] = Field(default_factory=list)
    rule_hint: str = ""

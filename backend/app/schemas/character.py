from __future__ import annotations

from pydantic import BaseModel, Field


class CharacterAttributesCreate(BaseModel):
    strength: int = Field(default=10, ge=1, le=30)
    dexterity: int = Field(default=10, ge=1, le=30)
    constitution: int = Field(default=10, ge=1, le=30)
    intelligence: int = Field(default=10, ge=1, le=30)
    wisdom: int = Field(default=10, ge=1, le=30)
    charisma: int = Field(default=10, ge=1, le=30)


class CharacterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    profession: str | None = Field(default=None, max_length=30)
    class_id: str | None = Field(default=None, max_length=30)
    race_id: str | None = Field(default=None, max_length=30)
    background_id: str | None = Field(default=None, max_length=30)
    motivation: str | None = None
    ability_assignment: str | None = Field(default=None, max_length=30)
    base_attributes: CharacterAttributesCreate | None = None
    selected_skills: list[str] = Field(default_factory=list)
    hp: int = Field(default=10, ge=1)
    max_hp: int = Field(default=10, ge=1)
    attributes: CharacterAttributesCreate = Field(default_factory=CharacterAttributesCreate)


class CharacterResponse(BaseModel):
    id: int
    name: str
    profession: str | None = None
    class_id: str | None = None
    race_id: str | None = None
    background_id: str | None = None
    motivation: str | None = None
    level: int = 1
    exp: int = 0
    hit_dice: str | None = None
    proficiency_bonus: int = 2
    hp: int
    max_hp: int
    attributes: CharacterAttributesCreate
    skills: dict = Field(default_factory=dict)
    saving_throws: list[str] = Field(default_factory=list)

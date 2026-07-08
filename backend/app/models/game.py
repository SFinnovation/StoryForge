"""跑团核心 ORM 模型 — 对齐 数据库存储结构设计.sql。"""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="user", nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str | None] = mapped_column(String)


class World(Base):
    __tablename__ = "worlds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, default="custom", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    opening_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    rule_style: Mapped[str | None] = mapped_column(String)
    difficulty: Mapped[str] = mapped_column(String, default="normal", nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    is_public: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    rulebook_pack_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("rulebook_packs.id"))
    adventure_module_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("adventure_modules.id"))
    created_at: Mapped[str | None] = mapped_column(String)


class RulebookPack(Base):
    """从 PHB 等规则书 docx 提取的标准化规则包。"""

    __tablename__ = "rulebook_packs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String)
    world_setting: Mapped[str] = mapped_column(Text, nullable=False)
    world_style: Mapped[str] = mapped_column(Text, nullable=False)
    public_world_facts_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    core_rules_summary: Mapped[str | None] = mapped_column(Text)
    extraction_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)
    created_at: Mapped[str | None] = mapped_column(String)


class AdventureModule(Base):
    """从冒险模组 docx 提取的结构化内容包。"""

    __tablename__ = "adventure_modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String)
    story_summary: Mapped[str] = mapped_column(Text, nullable=False)
    opening_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    scenes_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    current_scene: Mapped[str] = mapped_column(String, nullable=False)
    hidden_truths_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    world_facts_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    public_world_facts_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    player_known_clues_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    npc_private_facts_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    visible_npcs_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    seed_npcs_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    extraction_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)
    created_at: Mapped[str | None] = mapped_column(String)


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    profession: Mapped[str] = mapped_column(String, nullable=False)
    background: Mapped[str | None] = mapped_column(Text)
    motivation: Mapped[str | None] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    exp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hp: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_hp: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    inventory_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[str | None] = mapped_column(String)

    attributes: Mapped[CharacterAttributes | None] = relationship(
        back_populates="character", uselist=False
    )


class CharacterAttributes(Base):
    __tablename__ = "character_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("characters.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    strength: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dexterity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    constitution: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    intelligence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wisdom: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    charisma: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    character: Mapped[Character] = relationship(back_populates="attributes")


class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    world_id: Mapped[int] = mapped_column(Integer, ForeignKey("worlds.id"), nullable=False)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="playing", nullable=False)
    current_scene: Mapped[str | None] = mapped_column(String)
    current_task: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    clue_pressure: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    turns_since_key_clue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_checks_in_scene: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[str | None] = mapped_column(String)
    ended_at: Mapped[str | None] = mapped_column(String)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    sender_type: Mapped[str] = mapped_column(String, nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String, default="narration", nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str | None] = mapped_column(String)


class ActionCheck(Base):
    __tablename__ = "action_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("messages.id"))
    action_text: Mapped[str] = mapped_column(Text, nullable=False)
    check_type: Mapped[str] = mapped_column(String, nullable=False)
    skill_key: Mapped[str | None] = mapped_column(String)
    attribute_used: Mapped[str] = mapped_column(String, nullable=False)
    dc: Mapped[int] = mapped_column(Integer, nullable=False)
    dice_roll: Mapped[int] = mapped_column(Integer, nullable=False)
    attribute_bonus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skill_bonus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_value: Mapped[int] = mapped_column(Integer, nullable=False)
    is_success: Mapped[int] = mapped_column(Integer, nullable=False)
    result_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(String)


class Clue(Base):
    __tablename__ = "clues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_scene: Mapped[str | None] = mapped_column(String)
    importance: Mapped[str] = mapped_column(String, default="normal", nullable=False)
    discovered_at: Mapped[str | None] = mapped_column(String)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="todo", nullable=False)
    created_at: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[str | None] = mapped_column(String)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String)
    story_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_choices_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    clues_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    ending_type: Mapped[str] = mapped_column(String, default="open", nullable=False)
    character_growth: Mapped[str | None] = mapped_column(Text)
    ai_suggestion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(String)


class NpcProfile(Base):
    __tablename__ = "npc_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    npc_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    personality: Mapped[str | None] = mapped_column(Text)
    knowledge_scope_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    forbidden_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    speaking_style: Mapped[str | None] = mapped_column(String)
    alertness: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_scene: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str | None] = mapped_column(String)


class Fact(Base):
    __tablename__ = "facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    fact_type: Mapped[str] = mapped_column(String, nullable=False)
    visibility_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    related_scene: Mapped[str | None] = mapped_column(String)
    importance: Mapped[str] = mapped_column(String, default="normal", nullable=False)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)
    created_at: Mapped[str | None] = mapped_column(String)


class AiReview(Base):
    __tablename__ = "ai_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("messages.id"))
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    rule_score: Mapped[int | None] = mapped_column(Integer)
    world_score: Mapped[int | None] = mapped_column(Integer)
    context_score: Mapped[int | None] = mapped_column(Integer)
    character_score: Mapped[int | None] = mapped_column(Integer)
    npc_boundary_score: Mapped[int | None] = mapped_column(Integer)
    clue_score: Mapped[int | None] = mapped_column(Integer)
    approved: Mapped[int] = mapped_column(Integer, nullable=False)
    revision_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_fallback: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fatal_errors_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    revision_instructions_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[str | None] = mapped_column(String)

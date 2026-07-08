# -*- coding: utf-8 -*-
"""ORM 模型 — 与 schema.sql 一一对应的 9 张表

约定:
- 静态 D&D 5e 规则存于 rules/dnd5e/*.json, 不入库
- race_id/class_id/background_id 对应规则 JSON 的 id (如 'high-elf'/'rogue'/'acolyte')
- skills_json 的键与 action_checks.skill_key 使用 skills.json 的技能键 (如 'ste')
- attribute_used 与 saving_throws_json 使用 abilities.json 的 key (如 'dexterity')
"""
from datetime import datetime

from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(10), default="user", nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    characters: Mapped[list["Character"]] = relationship(back_populates="user")
    sessions: Mapped[list["GameSession"]] = relationship(back_populates="user")

    __table_args__ = (CheckConstraint("role IN ('user','admin')", name="ck_users_role"),)


class World(Base):
    __tablename__ = "worlds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    opening_prompt: Mapped[str | None] = mapped_column(Text)  # AI 开局 system 上下文
    rule_style: Mapped[str] = mapped_column(String(20), default="lite_dnd")
    difficulty: Mapped[str] = mapped_column(String(10), default="normal")
    cover_url: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_public: Mapped[int] = mapped_column(Integer, default=1)
    is_enabled: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("type IN ('fantasy','mystery','cyberpunk','custom')", name="ck_worlds_type"),
    )


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    race_id: Mapped[str | None] = mapped_column(String(30))       # dnd5e races.json id
    class_id: Mapped[str | None] = mapped_column(String(30))      # dnd5e classes.json id
    background_id: Mapped[str | None] = mapped_column(String(30)) # dnd5e backgrounds.json id
    motivation: Mapped[str | None] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer, default=1)
    exp: Mapped[int] = mapped_column(Integer, default=0)
    hp: Mapped[int] = mapped_column(Integer, default=10)
    max_hp: Mapped[int] = mapped_column(Integer, default=10)
    hit_dice: Mapped[str] = mapped_column(String(5), default="d8")
    proficiency_bonus: Mapped[int] = mapped_column(Integer, default=2)
    strength: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    dexterity: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    constitution: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    intelligence: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    wisdom: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    charisma: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    skills_json: Mapped[str] = mapped_column(Text, default="{}")
    saving_throws_json: Mapped[str] = mapped_column(Text, default="[]")
    inventory_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="characters")

    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 20", name="ck_characters_level"),
        CheckConstraint("strength BETWEEN 1 AND 30", name="ck_characters_str"),
        CheckConstraint("dexterity BETWEEN 1 AND 30", name="ck_characters_dex"),
        CheckConstraint("constitution BETWEEN 1 AND 30", name="ck_characters_con"),
        CheckConstraint("intelligence BETWEEN 1 AND 30", name="ck_characters_int"),
        CheckConstraint("wisdom BETWEEN 1 AND 30", name="ck_characters_wis"),
        CheckConstraint("charisma BETWEEN 1 AND 30", name="ck_characters_cha"),
    )


class GameSession(Base):
    """跑团会话 (表名 sessions; 类名避免与 sqlalchemy Session 混淆)"""
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), nullable=False)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(10), default="playing", nullable=False)
    current_scene: Mapped[str | None] = mapped_column(Text)
    current_task: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship(back_populates="sessions")
    world: Mapped["World"] = relationship()
    character: Mapped["Character"] = relationship()
    messages: Mapped[list["Message"]] = relationship(back_populates="session")
    action_checks: Mapped[list["ActionCheck"]] = relationship(back_populates="session")
    clues: Mapped[list["Clue"]] = relationship(back_populates="session")
    tasks: Mapped[list["Task"]] = relationship(back_populates="session")
    report: Mapped["Report | None"] = relationship(back_populates="session", uselist=False)

    __table_args__ = (
        CheckConstraint("status IN ('playing','finished','archived')", name="ck_sessions_status"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(10), nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["GameSession"] = relationship(back_populates="messages")

    __table_args__ = (
        CheckConstraint("sender_type IN ('player','ai','npc','system')", name="ck_messages_sender"),
        CheckConstraint("message_type IN ('narration','action','dialogue','dice','clue','task')",
                        name="ck_messages_type"),
    )


class ActionCheck(Base):
    __tablename__ = "action_checks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"))
    action_text: Mapped[str] = mapped_column(Text, nullable=False)
    check_type: Mapped[str | None] = mapped_column(String(20))
    skill_key: Mapped[str | None] = mapped_column(String(10))     # skills.json 键, 如 'ste'
    attribute_used: Mapped[str | None] = mapped_column(String(15))  # abilities.json key
    dc: Mapped[int | None] = mapped_column(Integer)
    dice_roll: Mapped[int | None] = mapped_column(Integer)
    ability_modifier: Mapped[int | None] = mapped_column(Integer)
    skill_bonus: Mapped[int] = mapped_column(Integer, default=0)
    final_value: Mapped[int | None] = mapped_column(Integer)
    is_success: Mapped[int | None] = mapped_column(Integer)
    result_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["GameSession"] = relationship(back_populates="action_checks")

    __table_args__ = (
        CheckConstraint("dc IS NULL OR dc BETWEEN 5 AND 30", name="ck_checks_dc"),
        CheckConstraint("dice_roll IS NULL OR dice_roll BETWEEN 1 AND 20", name="ck_checks_roll"),
    )


class Clue(Base):
    __tablename__ = "clues"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    source_scene: Mapped[str | None] = mapped_column(String(100))
    importance: Mapped[str] = mapped_column(String(10), default="normal")
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["GameSession"] = relationship(back_populates="clues")

    __table_args__ = (
        CheckConstraint("importance IN ('normal','important','key')", name="ck_clues_importance"),
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="todo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow,
                                                 onupdate=datetime.utcnow)

    session: Mapped["GameSession"] = relationship(back_populates="tasks")

    __table_args__ = (
        CheckConstraint("status IN ('todo','doing','done','failed')", name="ck_tasks_status"),
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(100))
    story_summary: Mapped[str | None] = mapped_column(Text)
    key_choices_json: Mapped[str] = mapped_column(Text, default="[]")
    clues_json: Mapped[str] = mapped_column(Text, default="[]")
    ending_type: Mapped[str | None] = mapped_column(String(10))
    character_growth: Mapped[str | None] = mapped_column(Text)
    ai_suggestion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["GameSession"] = relationship(back_populates="report")

    __table_args__ = (
        UniqueConstraint("session_id", name="uq_reports_session"),   # 与会话一对一
        CheckConstraint("ending_type IS NULL OR ending_type IN ('good','normal','bad','open')",
                        name="ck_reports_ending"),
    )

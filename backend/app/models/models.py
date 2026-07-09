# -*- coding: utf-8 -*-
"""ORM 模型 — 与 schema.sql 一一对应的数据库表定义

约定:
- 静态 D&D 5e 规则存于 rules/dnd5e/*.json, 不入库
- race_id/class_id/background_id 对应规则 JSON 的 id (如 'high-elf'/'rogue'/'acolyte')
- skills_json 的键与 action_checks.skill_key 使用 skills.json 的技能键 (如 'ste')
- attribute_used 与 saving_throws_json 使用 abilities.json 的 key (如 'dexterity')
"""
from datetime import datetime

from sqlalchemy import (CheckConstraint, DateTime, Float, ForeignKey, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    role: Mapped[str] = mapped_column(String(10), default="user", nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="active", nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    characters: Mapped[list["Character"]] = relationship(back_populates="user")
    sessions: Mapped[list["GameSession"]] = relationship(
        back_populates="user", foreign_keys="GameSession.user_id"
    )
    admin_logs: Mapped[list["AdminOperationLog"]] = relationship(back_populates="admin")

    __table_args__ = (
        CheckConstraint("role IN ('user','admin')", name="ck_users_role"),
        CheckConstraint("status IN ('active','banned')", name="ck_users_status"),
    )


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
    # ---- 内容提取包关联 (docs/ai-module-implementation §3.6/§3.7) ----
    rulebook_pack_id: Mapped[int | None] = mapped_column(ForeignKey("rulebook_packs.id"))
    adventure_module_id: Mapped[int | None] = mapped_column(ForeignKey("adventure_modules.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    modules: Mapped[list["WorldModule"]] = relationship(back_populates="world")

    __table_args__ = (
        CheckConstraint("type IN ('fantasy','mystery','cyberpunk','custom')", name="ck_worlds_type"),
    )

class WorldModule(Base):
    __tablename__ = "world_modules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_enabled: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    world: Mapped["World"] = relationship(back_populates="modules")

    __table_args__ = (
        CheckConstraint("is_enabled IN (0, 1)", name="ck_world_modules_enabled"),
    )


class RulebookPack(Base):
    """从 PHB 等规则书 docx 提取的标准化规则包 (RulebookExtractorAgent 落库)。"""

    __tablename__ = "rulebook_packs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255))
    world_setting: Mapped[str] = mapped_column(Text, nullable=False)
    world_style: Mapped[str] = mapped_column(Text, nullable=False)
    public_world_facts_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    core_rules_summary: Mapped[str | None] = mapped_column(Text)
    extraction_notes: Mapped[str | None] = mapped_column(Text)
    knowledge_pack_dir: Mapped[str | None] = mapped_column(String(500))  # AKP skill 包目录
    status: Mapped[str] = mapped_column(String(10), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AdventureModule(Base):
    """从冒险模组 docx 提取的结构化内容包 (ModuleExtractorAgent 落库)。"""

    __tablename__ = "adventure_modules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255))
    story_summary: Mapped[str] = mapped_column(Text, nullable=False)
    opening_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    scenes_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    current_scene: Mapped[str] = mapped_column(String(200), nullable=False)
    hidden_truths_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    world_facts_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    public_world_facts_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    player_known_clues_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    npc_private_facts_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    visible_npcs_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    seed_npcs_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    extraction_notes: Mapped[str | None] = mapped_column(Text)
    knowledge_pack_dir: Mapped[str | None] = mapped_column(String(500))  # AKP skill 包目录
    status: Mapped[str] = mapped_column(String(10), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
    """跑团会话 (表名 game_sessions, 与 ai-module-design §5.4/§11.2 一致)"""
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), nullable=False)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(10), default="playing", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(10), default="normal", nullable=False)
    current_scene: Mapped[str | None] = mapped_column(Text)
    current_task: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    # ---- AI 模块扩展字段 (ai-module-design §5.4) ----
    clue_pressure: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    turns_since_key_clue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    # ---- 多人房间扩展 (docs/multiplayer-realtime-design §3.7) ----
    # single: 沿用原单人闭环; multiplayer: 由 room host 建局, 成员通过 room_members 关联角色
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id"))
    mode: Mapped[str] = mapped_column(String(16), default="single", nullable=False)
    host_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(back_populates="sessions", foreign_keys=[user_id])
    world: Mapped["World"] = relationship()
    character: Mapped["Character"] = relationship()
    messages: Mapped[list["Message"]] = relationship(back_populates="session")
    action_checks: Mapped[list["ActionCheck"]] = relationship(back_populates="session")
    clues: Mapped[list["Clue"]] = relationship(back_populates="session")
    tasks: Mapped[list["Task"]] = relationship(back_populates="session")
    report: Mapped["Report | None"] = relationship(back_populates="session", uselist=False)
    # ---- AI 模块扩展关系 ----
    facts: Mapped[list["Fact"]] = relationship(back_populates="session")
    npc_profiles: Mapped[list["NpcProfile"]] = relationship(back_populates="session")
    ai_reviews: Mapped[list["AiReview"]] = relationship(back_populates="session")

    __table_args__ = (
        CheckConstraint("status IN ('playing','finished','archived')", name="ck_sessions_status"),
        CheckConstraint(
            "difficulty IN ('easy','normal','hard','nightmare')",
            name="ck_sessions_difficulty",
        ),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(10), nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(10), nullable=False)
    # ---- AI 旁白性能指标 (ai-module-design §8.2 第 4 步) ----
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
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
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"))
    scene: Mapped[str | None] = mapped_column(String(100))  # 检定发生场景, 供 count_failed_in_scene
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
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
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
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
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
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
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

# ============================================================
# AI 模块扩展表 (ai-module-design §11.2)
# ============================================================


class Fact(Base):
    """Fact 分层存储 (ai-module-design §4.2)

    - fact_type 六类: world_public / player_known / hidden_truth /
      npc_private / session_fact / temporary (MVP 用前三类 + npc_private)
    - visibility_json 例: {"player": false, "npcs": ["butler_001"], "dm": true}
    - status: locked(未解锁) -> active(生效中) -> resolved(已了结)
    """
    __tablename__ = "facts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    fact_type: Mapped[str] = mapped_column(String(20), nullable=False)
    visibility_json: Mapped[str] = mapped_column(Text, default='{"player": false, "npcs": [], "dm": true}')
    related_scene: Mapped[str | None] = mapped_column(String(100))
    importance: Mapped[str] = mapped_column(String(10), default="normal")
    status: Mapped[str] = mapped_column(String(10), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["GameSession"] = relationship(back_populates="facts")

    __table_args__ = (
        CheckConstraint(
            "fact_type IN ('world_public','player_known','hidden_truth',"
            "'npc_private','session_fact','temporary')",
            name="ck_facts_type"),
        CheckConstraint("importance IN ('normal','important','key')", name="ck_facts_importance"),
        CheckConstraint("status IN ('locked','active','resolved')", name="ck_facts_status"),
    )


class NpcProfile(Base):
    """NPC 人格与知识边界 (ai-module-design §4.3)

    MVP 不建独立 NPC Agent, 本表用于:
    - context_builder 组装 visible_npcs
    - critic_agent 检测 NPC 是否说出 forbidden_knowledge
    """
    __tablename__ = "npc_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    npc_id: Mapped[str] = mapped_column(String(50), nullable=False)  # 如 'butler_001'
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    personality: Mapped[str | None] = mapped_column(Text)
    knowledge_scope_json: Mapped[str] = mapped_column(Text, default="[]")
    forbidden_knowledge_json: Mapped[str] = mapped_column(Text, default="[]")
    speaking_style: Mapped[str | None] = mapped_column(String(100))
    related_scene: Mapped[str | None] = mapped_column(String(100))  # NpcRepo.list_visible 用
    is_visible: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    alertness: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # state_updates.npc_alertness
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["GameSession"] = relationship(back_populates="npc_profiles")

    __table_args__ = (
        UniqueConstraint("session_id", "npc_id", name="uq_npc_profiles_session_npc"),
        CheckConstraint("is_visible IN (0, 1)", name="ck_npc_visible"),
        CheckConstraint("alertness BETWEEN 0 AND 10", name="ck_npc_alertness"),
    )


class AiReview(Base):
    """Critic Agent 审核记录 (ai-module-design §6.5 / §8.2 第 9 步)

    scores_json 六维: rule_consistency / world_consistency / context_continuity /
    character_alignment / npc_knowledge_boundary / clue_progression
    """
    __tablename__ = "ai_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"))  # 关联最终 AI 旁白
    approved: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    scores_json: Mapped[str] = mapped_column(Text, default="{}")
    fatal_errors_json: Mapped[str] = mapped_column(Text, default="[]")
    revision_instructions_json: Mapped[str] = mapped_column(Text, default="[]")
    revision_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_fallback: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["GameSession"] = relationship(back_populates="ai_reviews")

    __table_args__ = (
        CheckConstraint("approved IN (0, 1)", name="ck_reviews_approved"),
        CheckConstraint("overall_score BETWEEN 0 AND 100", name="ck_reviews_score"),
        CheckConstraint("used_fallback IN (0, 1)", name="ck_reviews_fallback"),
    )


class AdminOperationLog(Base):
    __tablename__ = "admin_operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    admin: Mapped["User"] = relationship(back_populates="admin_logs")


# ============================================================
# 多人房间与实时跑团扩展表 (docs/multiplayer-realtime-design §3)
# ============================================================


class Room(Base):
    """多人协作容器。room 与 game_session 为 1:1（同时只推进一局）。"""

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)  # 加入用
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 无 FK 以打破 rooms<->game_sessions 循环外键（SQLite create_all 友好）
    current_session_id: Mapped[int | None] = mapped_column(Integer)
    visibility: Mapped[str] = mapped_column(String(10), default="private", nullable=False)
    status: Mapped[str] = mapped_column(String(12), default="waiting", nullable=False)
    max_players: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    invite_code: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    members: Mapped[list["RoomMember"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("visibility IN ('public','private')", name="ck_rooms_visibility"),
        CheckConstraint(
            "status IN ('waiting','playing','paused','finished','archived')",
            name="ck_rooms_status",
        ),
    )


class RoomMember(Base):
    __tablename__ = "room_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"))
    role: Mapped[str] = mapped_column(String(10), default="player", nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(50))
    online_status: Mapped[str] = mapped_column(String(10), default="offline", nullable=False)
    is_ready: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)

    room: Mapped["Room"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()
    character: Mapped["Character | None"] = relationship()

    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_room_members_room_user"),
        CheckConstraint("role IN ('host','player','spectator')", name="ck_room_members_role"),
        CheckConstraint(
            "online_status IN ('online','offline')", name="ck_room_members_online"
        ),
        CheckConstraint("is_ready IN (0, 1)", name="ck_room_members_ready"),
    )


class RoomMessage(Base):
    """房间实时事件流（聊天/系统/AI 广播镜像）。与叙事日志 messages 分离。"""

    __tablename__ = "room_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    session_id: Mapped[int | None] = mapped_column(Integer)
    sender_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    sender_role: Mapped[str] = mapped_column(String(10), nullable=False)  # user|ai_dm|system
    sender_name: Mapped[str | None] = mapped_column(String(50))
    message_type: Mapped[str] = mapped_column(String(12), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    client_msg_id: Mapped[str | None] = mapped_column(String(64))
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("room_id", "client_msg_id", name="uq_room_messages_client"),
        UniqueConstraint("room_id", "seq", name="uq_room_messages_seq"),
        CheckConstraint(
            "sender_role IN ('user','ai_dm','system')", name="ck_room_messages_role"
        ),
    )


class RoomAction(Base):
    """玩家提交的行动记录，用于幂等与（P2）队列。"""

    __tablename__ = "room_actions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    session_id: Mapped[int | None] = mapped_column(Integer)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    actor_character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"))
    action_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(12), default="pending", nullable=False)
    result_message_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','processing','done','rejected')",
            name="ck_room_actions_status",
        ),
    )

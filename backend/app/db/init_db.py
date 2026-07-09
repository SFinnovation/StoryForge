# -*- coding: utf-8 -*-
"""初始化建表 — 基于 ORM 元数据创建全部表与索引

用法:
    python -m app.db.init_db          # 建表(已存在则跳过)
    python -m app.db.init_db --drop   # 危险: 先删后建, 仅限开发环境
"""
import sys

from sqlalchemy import Index, inspect, text

from backend.app.core.config import settings
from backend.app.services.auth_service import hash_password, is_password_hash
from backend.app.db.database import Base, SessionLocal, engine
from backend.app.models import models  # noqa: F401  确保所有模型注册到 Base.metadata

# 索引定义(与 schema.sql 保持一致)
INDEXES = [
    Index("idx_sessions_user_status", models.GameSession.user_id, models.GameSession.status),
    Index("idx_messages_session", models.Message.session_id, models.Message.created_at),
    Index("idx_action_checks_session", models.ActionCheck.session_id),
    Index("idx_clues_session", models.Clue.session_id),
    Index("idx_tasks_session_status", models.Task.session_id, models.Task.status),
    Index("idx_characters_user", models.Character.user_id),
    Index("idx_world_modules_world_enabled", models.WorldModule.world_id, models.WorldModule.is_enabled),
    Index("idx_admin_logs_admin_created", models.AdminOperationLog.admin_id, models.AdminOperationLog.created_at),
    Index("idx_admin_logs_target", models.AdminOperationLog.target_type, models.AdminOperationLog.target_id),
    Index("idx_worlds_rulebook_pack", models.World.rulebook_pack_id),
    Index("idx_worlds_adventure_module", models.World.adventure_module_id),
    Index("idx_rulebook_packs_status", models.RulebookPack.status),
    Index("idx_adventure_modules_status", models.AdventureModule.status),
    # ---- AI 模块扩展表 (ai-module-design §11) ----
    # memory_retriever 按会话+类型取 Fact; context_builder 按场景取可见 NPC
    Index("idx_facts_session_type", models.Fact.session_id, models.Fact.fact_type),
    Index("idx_npc_profiles_session_scene", models.NpcProfile.session_id, models.NpcProfile.related_scene),
    Index("idx_ai_reviews_session", models.AiReview.session_id, models.AiReview.created_at),
    # ---- 多人房间扩展表 (multiplayer-realtime-design §3) ----
    Index("idx_rooms_owner_status", models.Room.owner_id, models.Room.status),
    Index("idx_room_members_room", models.RoomMember.room_id),
    Index("idx_room_members_user", models.RoomMember.user_id),
    Index("idx_room_messages_room_seq", models.RoomMessage.room_id, models.RoomMessage.seq),
    Index("idx_room_actions_room", models.RoomAction.room_id, models.RoomAction.status),
]

DEMO_USER_ID = 1


def _ensure_legacy_columns() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "users" not in table_names:
        return

    statements: list[str] = []

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "email" not in user_columns:
        statements.append("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
    if "status" not in user_columns:
        statements.append("ALTER TABLE users ADD COLUMN status VARCHAR(10) NOT NULL DEFAULT 'active'")
    if "is_temporary" not in user_columns:
        statements.append("ALTER TABLE users ADD COLUMN is_temporary INTEGER NOT NULL DEFAULT 0")

    if "worlds" in table_names:
        world_columns = {column["name"] for column in inspector.get_columns("worlds")}
        if "rulebook_pack_id" not in world_columns:
            statements.append("ALTER TABLE worlds ADD COLUMN rulebook_pack_id INTEGER")
        if "adventure_module_id" not in world_columns:
            statements.append("ALTER TABLE worlds ADD COLUMN adventure_module_id INTEGER")

    if "game_sessions" in table_names:
        session_columns = {column["name"] for column in inspector.get_columns("game_sessions")}
        if "room_id" not in session_columns:
            statements.append("ALTER TABLE game_sessions ADD COLUMN room_id INTEGER")
        if "mode" not in session_columns:
            statements.append(
                "ALTER TABLE game_sessions ADD COLUMN mode VARCHAR(16) NOT NULL DEFAULT 'single'"
            )
        if "host_user_id" not in session_columns:
            statements.append("ALTER TABLE game_sessions ADD COLUMN host_user_id INTEGER")
        if "difficulty" not in session_columns:
            statements.append("ALTER TABLE game_sessions ADD COLUMN difficulty VARCHAR(10) NOT NULL DEFAULT 'normal'")

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def _ensure_demo_user(db) -> None:
    demo = db.get(models.User, DEMO_USER_ID)
    if demo is not None:
        if not is_password_hash(demo.password_hash):
            demo.password_hash = hash_password("demo")
        demo.is_temporary = 0
        return
    db.add(
        models.User(
            id=DEMO_USER_ID,
            username=f"demo_user_{DEMO_USER_ID}",
            password_hash=hash_password("demo"),
            nickname="Demo User",
            role="user",
            status="active",
            is_temporary=0,
        )
    )


def _ensure_admin_user(db) -> None:
    admin = db.query(models.User).filter(models.User.username == settings.ADMIN_USERNAME).first()
    if admin is None:
        db.add(
            models.User(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                nickname="管理员",
                role="admin",
                status="active",
                is_temporary=0,
            )
        )
        return

    admin.role = "admin"
    admin.is_temporary = 0
    if getattr(admin, "status", None) != "active":
        admin.status = "active"


def _ensure_unique_builtin_admin_user(db) -> None:
    admin = db.query(models.User).filter(models.User.username == settings.ADMIN_USERNAME).first()
    if admin is None:
        admin = models.User(
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            nickname="Admin_Root",
            role="admin",
            status="active",
            is_temporary=0,
        )
        db.add(admin)
    else:
        admin.role = "admin"
        admin.status = "active"
        admin.is_temporary = 0
        admin.nickname = "Admin_Root"
        admin.password_hash = hash_password(settings.ADMIN_PASSWORD)

    other_admins = (
        db.query(models.User)
        .filter(models.User.role == "admin", models.User.username != settings.ADMIN_USERNAME)
        .all()
    )
    for user in other_admins:
        user.role = "user"


def init_db(drop_first: bool = False) -> None:
    from backend.app.models import chapter, story, worldbuilding  # noqa: F401

    if drop_first:
        Base.metadata.drop_all(bind=engine)
        print("已删除所有旧表")
    Base.metadata.create_all(bind=engine)
    _ensure_legacy_columns()
    with SessionLocal() as db:
        _ensure_demo_user(db)
        _ensure_unique_builtin_admin_user(db)
        db.commit()
    tables = sorted(Base.metadata.tables.keys())
    print(f"建表完成({len(tables)} 张): {', '.join(tables)}")


def seed_demo_data() -> None:
    demo_worlds = [
        {
            "id": 1,
            "name": "COC 7th",
            "type": "mystery",
            "description": "调查、悬疑与不可名状，适合推理和氛围感团本。",
            "opening_prompt": "Open a concise COC investigation scene with mystery and tension.",
            "rule_style": "lite_coc",
        },
        {
            "id": 2,
            "name": "龙与地下城 DND",
            "type": "fantasy",
            "description": "从城堡、地下城到巨龙阴影，适合长期剧情推进与团队成长。",
            "opening_prompt": "Open a concise D&D fantasy adventure scene.",
            "rule_style": "dnd5e",
        },
        {
            "id": 3,
            "name": "自定义世界观",
            "type": "custom",
            "description": "原创规则与世界自由搭建，从设定开始你的跑团。",
            "opening_prompt": "Open a concise custom-world adventure based on the player's premise.",
            "rule_style": "custom",
        },
    ]

    with SessionLocal() as db:
        _ensure_demo_user(db)

        for item in demo_worlds:
            world = db.get(models.World, item["id"])
            if world is None:
                db.add(
                    models.World(
                        id=item["id"],
                        name=item["name"],
                        type=item["type"],
                        description=item["description"],
                        opening_prompt=item["opening_prompt"],
                        rule_style=item["rule_style"],
                        difficulty="normal",
                        created_by=1,
                    )
                )
            else:
                world.name = item["name"]
                world.type = item["type"]
                if not world.rulebook_pack_id and not world.adventure_module_id:
                    world.description = item["description"]
                    world.opening_prompt = item["opening_prompt"]
                    world.rule_style = item["rule_style"]
                world.difficulty = "normal"
                world.created_by = world.created_by or 1
                world.is_enabled = 1

        if db.get(models.Character, 1) is None:
            db.add(
                models.Character(
                    id=1,
                    user_id=1,
                    name="Demo Hero",
                    race_id="human",
                    class_id="investigator",
                    background_id="scholar",
                    motivation="Follow the missing clues.",
                    level=1,
                    hp=10,
                    max_hp=10,
                    strength=10,
                    dexterity=12,
                    constitution=10,
                    intelligence=14,
                    wisdom=14,
                    charisma=11,
                    skills_json='{"prc": true, "inv": true}',
                )
            )

        if db.get(models.GameSession, 1) is None:
            db.add(
                models.GameSession(
                    id=1,
                    user_id=1,
                    world_id=2,
                    character_id=1,
                    title="Demo Session",
                    status="playing",
                    difficulty="normal",
                    current_scene="main_hall",
                    current_task="Find the first clue",
                    summary="",
                )
            )

        db.commit()


def reset_demo_db() -> None:
    init_db(drop_first=True)
    seed_demo_data()


if __name__ == "__main__":
    init_db(drop_first="--drop" in sys.argv)

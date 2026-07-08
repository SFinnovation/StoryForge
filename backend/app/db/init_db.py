# -*- coding: utf-8 -*-
"""初始化建表 — 基于 ORM 元数据创建全部 12 张表与索引

用法:
    python -m app.db.init_db          # 建表(已存在则跳过)
    python -m app.db.init_db --drop   # 危险: 先删后建, 仅限开发环境
"""
import sys

from sqlalchemy import Index

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
    # ---- AI 模块扩展表 (ai-module-design §11) ----
    # memory_retriever 按会话+类型取 Fact; context_builder 按场景取可见 NPC
    Index("idx_facts_session_type", models.Fact.session_id, models.Fact.fact_type),
    Index("idx_npc_profiles_session_scene", models.NpcProfile.session_id, models.NpcProfile.related_scene),
    Index("idx_ai_reviews_session", models.AiReview.session_id, models.AiReview.created_at),
]

DEMO_USER_ID = 1


def _ensure_demo_user(db) -> None:
    if db.get(models.User, DEMO_USER_ID) is not None:
        return
    db.add(
        models.User(
            id=DEMO_USER_ID,
            username=f"demo_user_{DEMO_USER_ID}",
            password_hash="demo",
            nickname="Demo User",
            role="user",
        )
    )


def init_db(drop_first: bool = False) -> None:
    if drop_first:
        Base.metadata.drop_all(bind=engine)
        print("已删除所有旧表")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        _ensure_demo_user(db)
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

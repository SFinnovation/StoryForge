<<<<<<< HEAD
# -*- coding: utf-8 -*-
"""初始化建表 — 基于 ORM 元数据创建全部 9 张表与索引

用法:
    python -m app.db.init_db          # 建表(已存在则跳过)
    python -m app.db.init_db --drop   # 危险: 先删后建, 仅限开发环境
"""
import sys

from sqlalchemy import Index

from .database import Base, engine
from backend.app.models import models  # noqa: F401  确保所有模型注册到 Base.metadata

# 索引定义(与 schema.sql 保持一致)
INDEXES = [
    Index("idx_sessions_user_status", models.GameSession.user_id, models.GameSession.status),
    Index("idx_messages_session", models.Message.session_id, models.Message.created_at),
    Index("idx_action_checks_session", models.ActionCheck.session_id),
    Index("idx_clues_session", models.Clue.session_id),
    Index("idx_tasks_session_status", models.Task.session_id, models.Task.status),
    Index("idx_characters_user", models.Character.user_id),
]


def init_db(drop_first: bool = False) -> None:
    if drop_first:
        Base.metadata.drop_all(bind=engine)
        print("已删除所有旧表")
    Base.metadata.create_all(bind=engine)
    tables = sorted(Base.metadata.tables.keys())
    print(f"建表完成({len(tables)} 张): {', '.join(tables)}")


if __name__ == "__main__":
    init_db(drop_first="--drop" in sys.argv)
=======
"""数据库初始化与种子数据。"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import event, text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from app.models.game import (
    Character,
    CharacterAttributes,
    GameSession,
    User,
    World,
)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    if engine.url.get_backend_name() == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        _seed_if_empty(db)


def _seed_if_empty(db: Session) -> None:
    if db.query(User).first():
        return

    demo_user = User(
        username="demo",
        password_hash="demo-hash",
        nickname="演示用户",
        role="user",
        created_at=_now(),
    )
    db.add(demo_user)
    db.flush()

    worlds = [
        World(
            name="奇幻遗迹",
            type="fantasy",
            description="古老遗迹中沉睡着失落的魔法文明。",
            opening_prompt="奇幻冒险，遗迹探索，魔法与危险并存。",
            rule_style="lite_dnd",
            difficulty="normal",
            is_public=1,
            is_active=1,
            created_at=_now(),
        ),
        World(
            name="古堡悬疑",
            type="mystery",
            description="黑鸦古堡笼罩在浓雾与谜团之中，失踪学者的线索指向这里。",
            opening_prompt="古堡悬疑，调查推理，不要相信钟声之后出现的人。",
            rule_style="lite_dnd",
            difficulty="normal",
            is_public=1,
            is_active=1,
            created_at=_now(),
        ),
    ]
    db.add_all(worlds)
    db.flush()

    character = Character(
        user_id=demo_user.id,
        name="艾琳",
        profession="调查员",
        background="研究失踪案件的年轻侦探",
        motivation="寻找失踪学者留下的最后一份手稿",
        hp=10,
        max_hp=10,
        created_at=_now(),
    )
    db.add(character)
    db.flush()

    db.add(
        CharacterAttributes(
            character_id=character.id,
            strength=0,
            dexterity=2,
            constitution=1,
            intelligence=2,
            wisdom=3,
            charisma=1,
        )
    )
    db.commit()


def reset_demo_db() -> None:
    """测试用：清空并重建。"""
    Base.metadata.drop_all(bind=engine)
    init_db()
>>>>>>> 38f0109237ad6b65c9edd640994015f91dcc4f4e

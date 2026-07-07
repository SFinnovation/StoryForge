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

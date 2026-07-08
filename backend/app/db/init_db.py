# -*- coding: utf-8 -*-
"""Initialize database tables from ORM metadata.

Usage:
    python -m app.db.init_db
    python -m app.db.init_db --drop
"""

from __future__ import annotations

import sys

from sqlalchemy import Index

from .database import Base, engine
from backend.app.models import models  # noqa: F401 - register models in Base.metadata


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
        print("Dropped existing tables.")

    Base.metadata.create_all(bind=engine)
    tables = sorted(Base.metadata.tables.keys())
    print(f"Created tables ({len(tables)}): {', '.join(tables)}")


if __name__ == "__main__":
    init_db(drop_first="--drop" in sys.argv)

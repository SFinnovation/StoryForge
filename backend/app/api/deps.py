from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.db.database import get_db

DEMO_USER_ID = 1


def get_current_user_id() -> int:
    """MVP：演示用户 ID；接入 JWT 后替换为 token 解析。"""
    return DEMO_USER_ID


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db

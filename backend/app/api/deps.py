from fastapi import Depends, Header
from sqlalchemy.orm import Session

from backend.app.core.exceptions import StoryForgeError
from backend.app.db.database import get_db
from backend.app.services.auth_service import decode_access_token

DEMO_USER_ID = 1


def get_current_user_id(authorization: str | None = Header(default=None)) -> int:
    """解析 Bearer token；无 token 时保留 demo 用户以兼容本地 mock 脚本。"""
    if authorization is None:
        return DEMO_USER_ID
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise StoryForgeError("invalid authorization header", status_code=401)
    return decode_access_token(token).user_id


def get_optional_user_id(authorization: str | None = Header(default=None)) -> int:
    if authorization is None:
        return DEMO_USER_ID
    return get_current_user_id(authorization)


def get_demo_user_id() -> int:
    return DEMO_USER_ID


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db

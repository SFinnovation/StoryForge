from fastapi import Depends, Header
from sqlalchemy.orm import Session

from backend.app.core.exceptions import StoryForgeError
from backend.app.db.database import get_db
from backend.app.models.models import User
from backend.app.services.auth_service import decode_access_token

DEMO_USER_ID = 1


def _decode_bearer_user_id(authorization: str | None) -> int:
    if authorization is None:
        raise StoryForgeError("authorization required", status_code=401)
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise StoryForgeError("invalid authorization header", status_code=401)
    return decode_access_token(token).user_id


def get_current_user_id(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> int:
    if authorization is None:
        return DEMO_USER_ID

    user_id = _decode_bearer_user_id(authorization)
    user = db.get(User, user_id)
    if user is None:
        raise StoryForgeError("user not found", status_code=404)
    if user.status != "active":
        raise StoryForgeError("account is banned", status_code=403)
    return user.id


def get_optional_user_id(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> int:
    if authorization is None:
        return DEMO_USER_ID
    return get_current_user_id(authorization, db)


def get_current_admin_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    user_id = _decode_bearer_user_id(authorization)
    user = db.get(User, user_id)
    if user is None:
        raise StoryForgeError("user not found", status_code=404)
    if user.status != "active":
        raise StoryForgeError("account is banned", status_code=403)
    if user.role != "admin":
        raise StoryForgeError("admin permission required", status_code=403)
    return user


def get_demo_user_id() -> int:
    return DEMO_USER_ID


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_id, get_db_session
from backend.app.core.exceptions import StoryForgeError
from backend.app.models.models import User
from backend.app.schemas.api_response import success
from backend.app.services.auth_service import (
    create_access_token,
    hash_password,
    needs_password_rehash,
    verify_legacy_plaintext_password,
    verify_password,
)
from backend.app.services.temporary_user_service import cleanup_temporary_user, create_guest_user

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    nickname: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "is_temporary": bool(getattr(user, "is_temporary", 0)),
        "avatar_url": user.avatar_url,
    }


def _token_payload(user: User) -> dict:
    return {
        "access_token": create_access_token(user_id=user.id, username=user.username),
        "token_type": "bearer",
        "user": _user_payload(user),
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db_session)):
    exists = db.query(User).filter(User.username == payload.username).first()
    if exists is not None:
        raise StoryForgeError("username already exists", status_code=409)
    if payload.email:
        email_exists = db.query(User).filter(User.email == payload.email).first()
        if email_exists is not None:
            raise StoryForgeError("email already exists", status_code=409)
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname or payload.username,
        email=payload.email,
        role="user",
        status="active",
        is_temporary=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success(_token_payload(user), message="registered")


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db_session)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None:
        raise StoryForgeError("invalid username or password", status_code=401)

    password_ok = verify_password(payload.password, user.password_hash)
    legacy_plaintext_ok = False
    if not password_ok:
        legacy_plaintext_ok = verify_legacy_plaintext_password(payload.password, user.password_hash)
        password_ok = legacy_plaintext_ok
    if not password_ok:
        raise StoryForgeError("invalid username or password", status_code=401)

    if user.status != "active":
        raise StoryForgeError("account is banned", status_code=403)
    if legacy_plaintext_ok or needs_password_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
        db.commit()
        db.refresh(user)
    return success(_token_payload(user), message="logged in")


@router.post("/guest", status_code=status.HTTP_201_CREATED)
def guest_login(db: Session = Depends(get_db_session)):
    user = create_guest_user(db)
    return success(_token_payload(user), message="guest created")


@router.post("/logout")
def logout(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    deleted = cleanup_temporary_user(db, user_id)
    return success({"temporary_deleted": deleted}, message="logged out")


@router.get("/me")
def me(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    user = db.get(User, user_id)
    if user is None:
        raise StoryForgeError("user not found", status_code=404)
    return success(_user_payload(user))

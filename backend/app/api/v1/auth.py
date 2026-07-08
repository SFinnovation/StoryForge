from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_id, get_db_session
from backend.app.core.exceptions import StoryForgeError
from backend.app.models.models import User
from backend.app.schemas.api_response import success
from backend.app.services.auth_service import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    nickname: str | None = Field(default=None, max_length=50)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "role": user.role,
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
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname or payload.username,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success(_token_payload(user), message="registered")


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db_session)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise StoryForgeError("invalid username or password", status_code=401)
    return success(_token_payload(user), message="logged in")


@router.get("/me")
def me(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
):
    user = db.get(User, user_id)
    if user is None:
        raise StoryForgeError("user not found", status_code=404)
    return success(_user_payload(user))

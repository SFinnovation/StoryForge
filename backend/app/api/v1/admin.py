from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_admin_user, get_db_session
from backend.app.core.exceptions import StoryForgeError
from backend.app.models.models import AdminOperationLog, GameSession, Message, Report, User, World, WorldModule
from backend.app.schemas.api_response import success
from backend.app.services.auth_service import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminWorldModuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class AdminWorldCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: Literal["fantasy", "mystery", "cyberpunk", "custom"] = "custom"
    description: str | None = None
    opening_prompt: str | None = None
    rule_style: str = Field(default="custom", max_length=20)
    difficulty: str = Field(default="normal", max_length=10)
    cover_url: str | None = Field(default=None, max_length=255)
    is_public: bool = True
    modules: list[AdminWorldModuleCreate] = Field(default_factory=list)


class AdminSessionDissolveRequest(BaseModel):
    reason: str = Field(default="违规会话", max_length=500)


class AdminPasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)
    reason: str | None = Field(default=None, max_length=500)


class AdminUserStatusRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


def _bool_int(value: bool) -> int:
    return 1 if value else 0


def _write_log(
    db: Session,
    admin: User,
    *,
    action: str,
    target_type: str | None,
    target_id: int | None,
    description: str,
) -> AdminOperationLog:
    log = AdminOperationLog(
        admin_id=admin.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        description=description,
    )
    db.add(log)
    return log


def _module_payload(module: WorldModule) -> dict:
    return {
        "id": module.id,
        "world_id": module.world_id,
        "name": module.name,
        "description": module.description,
        "is_enabled": bool(module.is_enabled),
        "created_by": module.created_by,
        "created_at": module.created_at,
    }


def _world_payload(world: World, *, include_disabled_modules: bool = False) -> dict:
    modules = list(world.modules or [])
    if not include_disabled_modules:
        modules = [module for module in modules if module.is_enabled]
    return {
        "id": world.id,
        "name": world.name,
        "type": world.type,
        "description": world.description,
        "opening_prompt": world.opening_prompt,
        "rule_style": world.rule_style,
        "difficulty": world.difficulty,
        "cover_url": world.cover_url,
        "created_by": world.created_by,
        "is_public": bool(world.is_public),
        "is_enabled": bool(world.is_enabled),
        "created_at": world.created_at,
        "modules": [_module_payload(module) for module in modules],
    }


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "password_hash": user.password_hash,
        "role": user.role,
        "status": user.status,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
    }


def _message_payload(message: Message) -> dict:
    return {
        "id": message.id,
        "session_id": message.session_id,
        "sender_type": message.sender_type,
        "sender_name": message.sender_name,
        "content": message.content,
        "message_type": message.message_type,
        "tokens_used": message.tokens_used,
        "latency_ms": message.latency_ms,
        "created_at": message.created_at,
    }


def _session_payload(session: GameSession, *, include_messages: bool = False) -> dict:
    data = {
        "id": session.id,
        "owner_id": session.user_id,
        "owner": {
            "id": session.user.id,
            "username": session.user.username,
            "nickname": session.user.nickname,
        }
        if session.user
        else None,
        "world_id": session.world_id,
        "world_name": session.world.name if session.world else None,
        "character_id": session.character_id,
        "title": session.title,
        "status": session.status,
        "current_scene": session.current_scene,
        "current_task": session.current_task,
        "summary": session.summary,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "message_count": len(session.messages or []),
    }
    if include_messages:
        data["messages"] = [_message_payload(message) for message in sorted(session.messages, key=lambda item: item.id)]
    return data


@router.get("/summary")
def get_admin_summary(
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    return success(
        {
            "users": db.query(func.count(User.id)).scalar() or 0,
            "banned_users": db.query(func.count(User.id)).filter(User.status == "banned").scalar() or 0,
            "worlds": db.query(func.count(World.id)).filter(World.is_enabled == 1).scalar() or 0,
            "modules": db.query(func.count(WorldModule.id)).filter(WorldModule.is_enabled == 1).scalar() or 0,
            "sessions": db.query(func.count(GameSession.id)).scalar() or 0,
            "active_sessions": db.query(func.count(GameSession.id)).filter(GameSession.status == "playing").scalar() or 0,
            "reports": db.query(func.count(Report.id)).scalar() or 0,
        }
    )


@router.get("/worlds")
def list_admin_worlds(
    include_disabled: bool = Query(default=False),
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(World).options(joinedload(World.modules)).order_by(World.id.desc())
    if not include_disabled:
        query = query.filter(World.is_enabled == 1)
    worlds = query.all()
    return success({"items": [_world_payload(world, include_disabled_modules=include_disabled) for world in worlds]})


@router.post("/worlds", status_code=status.HTTP_201_CREATED)
def create_admin_world(
    payload: AdminWorldCreate,
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    world = World(
        name=payload.name,
        type=payload.type,
        description=payload.description,
        opening_prompt=payload.opening_prompt,
        rule_style=payload.rule_style,
        difficulty=payload.difficulty,
        cover_url=payload.cover_url,
        created_by=admin.id,
        is_public=_bool_int(payload.is_public),
        is_enabled=1,
    )
    db.add(world)
    db.flush()

    for item in payload.modules:
        db.add(
            WorldModule(
                world_id=world.id,
                name=item.name,
                description=item.description,
                created_by=admin.id,
                is_enabled=1,
            )
        )

    _write_log(
        db,
        admin,
        action="create_world",
        target_type="world",
        target_id=world.id,
        description=f"管理员 {admin.id} 新增世界观 {world.name}",
    )
    db.commit()
    db.refresh(world)
    return success(_world_payload(world), message="world created")


@router.delete("/worlds/{world_id}")
def delete_admin_world(
    world_id: int,
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    world = db.get(World, world_id)
    if world is None:
        raise StoryForgeError("world not found", status_code=404)

    world.is_enabled = 0
    for module in world.modules:
        module.is_enabled = 0

    _write_log(
        db,
        admin,
        action="delete_world",
        target_type="world",
        target_id=world.id,
        description=f"管理员 {admin.id} 删除世界观 {world.name}",
    )
    db.commit()
    return success({"id": world.id, "is_enabled": False}, message="world deleted")


@router.post("/worlds/{world_id}/modules", status_code=status.HTTP_201_CREATED)
def create_admin_module(
    world_id: int,
    payload: AdminWorldModuleCreate,
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    world = db.get(World, world_id)
    if world is None or not world.is_enabled:
        raise StoryForgeError("world not found", status_code=404)

    exists = (
        db.query(WorldModule)
        .filter(WorldModule.world_id == world_id, WorldModule.name == payload.name, WorldModule.is_enabled == 1)
        .first()
    )
    if exists is not None:
        raise StoryForgeError("module already exists", status_code=409)

    module = WorldModule(
        world_id=world_id,
        name=payload.name,
        description=payload.description,
        created_by=admin.id,
        is_enabled=1,
    )
    db.add(module)
    db.flush()
    _write_log(
        db,
        admin,
        action="create_module",
        target_type="module",
        target_id=module.id,
        description=f"管理员 {admin.id} 在世界观 {world.name} 下新增模组 {module.name}",
    )
    db.commit()
    db.refresh(module)
    return success(_module_payload(module), message="module created")


@router.delete("/modules/{module_id}")
def delete_admin_module(
    module_id: int,
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    module = db.get(WorldModule, module_id)
    if module is None:
        raise StoryForgeError("module not found", status_code=404)

    module.is_enabled = 0
    _write_log(
        db,
        admin,
        action="delete_module",
        target_type="module",
        target_id=module.id,
        description=f"管理员 {admin.id} 删除模组 {module.name}",
    )
    db.commit()
    return success({"id": module.id, "is_enabled": False}, message="module deleted")


@router.get("/sessions")
def list_admin_sessions(
    owner_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    world_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None, max_length=100),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(GameSession).options(
        joinedload(GameSession.user),
        joinedload(GameSession.world),
        joinedload(GameSession.messages),
    )

    if owner_id is not None:
        query = query.filter(GameSession.user_id == owner_id)
    if status_filter:
        query = query.filter(GameSession.status == status_filter)
    if world_id is not None:
        query = query.filter(GameSession.world_id == world_id)
    if created_from is not None:
        query = query.filter(GameSession.started_at >= created_from)
    if created_to is not None:
        query = query.filter(GameSession.started_at <= created_to)
    if keyword:
        like = f"%{keyword}%"
        query = query.join(User, GameSession.user_id == User.id).filter(
            or_(GameSession.title.ilike(like), User.username.ilike(like), User.nickname.ilike(like))
        )

    total = query.count()
    sessions = query.order_by(GameSession.started_at.desc(), GameSession.id.desc()).offset(skip).limit(limit).all()
    return success({"total": total, "items": [_session_payload(session) for session in sessions]})


@router.get("/sessions/{session_id}")
def get_admin_session_detail(
    session_id: int,
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    session = (
        db.query(GameSession)
        .options(
            joinedload(GameSession.user),
            joinedload(GameSession.world),
            joinedload(GameSession.messages),
        )
        .filter(GameSession.id == session_id)
        .first()
    )
    if session is None:
        raise StoryForgeError("session not found", status_code=404)
    return success(_session_payload(session, include_messages=True))


@router.post("/sessions/{session_id}/dissolve")
def dissolve_admin_session(
    session_id: int,
    payload: AdminSessionDissolveRequest,
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    session = db.get(GameSession, session_id)
    if session is None:
        raise StoryForgeError("session not found", status_code=404)

    session.status = "archived"
    session.ended_at = datetime.utcnow()
    db.add(
        Message(
            session_id=session.id,
            sender_type="system",
            sender_name="admin",
            content=f"管理员强制解散会话：{payload.reason}",
            message_type="narration",
        )
    )
    _write_log(
        db,
        admin,
        action="dissolve_session",
        target_type="session",
        target_id=session.id,
        description=f"管理员 {admin.id} 强制解散会话 {session.id}，原因：{payload.reason}",
    )
    db.commit()
    return success({"id": session.id, "status": session.status}, message="session dissolved")


@router.get("/users")
def list_admin_users(
    user_id: int | None = Query(default=None),
    nickname: str | None = Query(default=None, max_length=50),
    email: str | None = Query(default=None, max_length=255),
    status_filter: str | None = Query(default=None, alias="status"),
    role: str | None = Query(default=None, max_length=10),
    keyword: str | None = Query(default=None, max_length=100),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(User)

    if user_id is not None:
        query = query.filter(User.id == user_id)
    if nickname:
        query = query.filter(User.nickname.ilike(f"%{nickname}%"))
    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))
    if status_filter:
        query = query.filter(User.status == status_filter)
    if role:
        query = query.filter(User.role == role)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(User.username.ilike(like), User.nickname.ilike(like), User.email.ilike(like)))

    total = query.count()
    users = query.order_by(User.id.desc()).offset(skip).limit(limit).all()
    return success({"total": total, "items": [_user_payload(user) for user in users]})


@router.post("/users/{user_id}/reset-password")
def reset_admin_user_password(
    user_id: int,
    payload: AdminPasswordResetRequest,
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    user = db.get(User, user_id)
    if user is None:
        raise StoryForgeError("user not found", status_code=404)

    user.password_hash = hash_password(payload.new_password)
    reason = f"，原因：{payload.reason}" if payload.reason else ""
    _write_log(
        db,
        admin,
        action="reset_user_password",
        target_type="user",
        target_id=user.id,
        description=f"管理员 {admin.id} 重置用户 {user.id} 的密码{reason}",
    )
    db.commit()
    return success(_user_payload(user), message="password reset")


@router.post("/users/{user_id}/ban")
def ban_admin_user(
    user_id: int,
    payload: AdminUserStatusRequest,
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    if user_id == admin.id:
        raise StoryForgeError("cannot ban current admin", status_code=409)
    user = db.get(User, user_id)
    if user is None:
        raise StoryForgeError("user not found", status_code=404)

    user.status = "banned"
    reason = f"，原因：{payload.reason}" if payload.reason else ""
    _write_log(
        db,
        admin,
        action="ban_user",
        target_type="user",
        target_id=user.id,
        description=f"管理员 {admin.id} 封禁用户 {user.id}{reason}",
    )
    db.commit()
    return success(_user_payload(user), message="user banned")


@router.post("/users/{user_id}/unban")
def unban_admin_user(
    user_id: int,
    payload: AdminUserStatusRequest,
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    user = db.get(User, user_id)
    if user is None:
        raise StoryForgeError("user not found", status_code=404)

    user.status = "active"
    reason = f"，原因：{payload.reason}" if payload.reason else ""
    _write_log(
        db,
        admin,
        action="unban_user",
        target_type="user",
        target_id=user.id,
        description=f"管理员 {admin.id} 解封用户 {user.id}{reason}",
    )
    db.commit()
    return success(_user_payload(user), message="user unbanned")


@router.get("/operation-logs")
def list_admin_operation_logs(
    admin_id: int | None = Query(default=None),
    action: str | None = Query(default=None, max_length=50),
    target_type: str | None = Query(default=None, max_length=50),
    target_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(AdminOperationLog).options(joinedload(AdminOperationLog.admin))

    if admin_id is not None:
        query = query.filter(AdminOperationLog.admin_id == admin_id)
    if action:
        query = query.filter(AdminOperationLog.action == action)
    if target_type:
        query = query.filter(AdminOperationLog.target_type == target_type)
    if target_id is not None:
        query = query.filter(AdminOperationLog.target_id == target_id)

    total = query.count()
    logs = (
        query.order_by(AdminOperationLog.created_at.desc(), AdminOperationLog.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return success(
        {
            "total": total,
            "items": [
                {
                    "id": log.id,
                    "admin_id": log.admin_id,
                    "admin_username": log.admin.username if log.admin else None,
                    "action": log.action,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "description": log.description,
                    "created_at": log.created_at,
                }
                for log in logs
            ],
        }
    )

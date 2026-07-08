# -*- coding: utf-8 -*-
"""房间成员服务 (docs/multiplayer-realtime-design §4 / §6)

加入 / 退出 / 准备 / 选择角色 / 在线状态。均为同步 DB 操作，广播由调用方（路由或
WS 处理器）在提交成功后触发。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.core.exceptions import StoryForgeError
from datetime import datetime

from backend.app.models.models import Character, GameSession, RoomMember, User
from backend.app.repositories.room_repository import RoomMemberRepo, RoomRepo
from backend.app.schemas.room_schema import RoomJoinRequest
from backend.app.services.room_service import get_room


def _validate_character(db: Session, user_id: int, character_id: int | None) -> Character | None:
    if character_id is None:
        return None
    character = db.get(Character, character_id)
    if character is None or character.user_id != user_id:
        raise StoryForgeError("character not found", status_code=404)
    return character


def join_room(db: Session, user_id: int, payload: RoomJoinRequest) -> tuple[int, RoomMember, bool]:
    """返回 (room_id, member, is_new)。is_new=False 表示重复加入（幂等）。"""
    room = RoomRepo(db).get_by_code(payload.room_code.strip().upper())
    if room is None:
        raise StoryForgeError("room not found", status_code=404)
    if room.status in ("finished", "archived"):
        raise StoryForgeError("room is closed", status_code=409)

    members = RoomMemberRepo(db)
    existing = members.get(room.id, user_id)
    if existing is not None:
        return room.id, existing, False

    if members.count(room.id) >= room.max_players:
        raise StoryForgeError("room is full", status_code=409)

    _validate_character(db, user_id, payload.character_id)
    user = db.get(User, user_id)
    display_name = payload.display_name or (user.nickname or user.username if user else None)

    try:
        member = members.add(
            room_id=room.id,
            user_id=user_id,
            role="player",
            display_name=display_name,
            character_id=payload.character_id,
        )
        RoomRepo(db).touch(room)
        db.commit()
        db.refresh(member)
    except Exception:
        db.rollback()
        raise
    return room.id, member, True


def leave_room(db: Session, room_id: int, user_id: int) -> dict:
    """退出房间并处理 host 转让/解散。

    返回:
    {
      "removed": bool,
      "transferred_to_user_id": int | None,
      "room_dissolved": bool,
    }
    """
    room = get_room(db, room_id)
    room_repo = RoomRepo(db)
    members = RoomMemberRepo(db)
    member = members.get(room_id, user_id)
    if member is None:
        return {"removed": False, "transferred_to_user_id": None, "room_dissolved": False}
    transferred_to_user_id: int | None = None
    room_dissolved = False
    try:
        db.delete(member)
        db.flush()

        if member.role == "host":
            remain = members.list_by_room(room_id)
            if remain:
                new_host = remain[0]
                new_host.role = "host"
                room.owner_id = new_host.user_id
                transferred_to_user_id = new_host.user_id
            else:
                room.status = "archived"
                room.current_session_id = None
                room_dissolved = True

            if room.current_session_id:
                session = db.get(GameSession, room.current_session_id)
                if session is not None and session.status == "playing":
                    session.status = "finished"
                    session.ended_at = datetime.utcnow()

        room_repo.touch(room)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "removed": True,
        "transferred_to_user_id": transferred_to_user_id,
        "room_dissolved": room_dissolved,
    }


def set_ready(db: Session, room_id: int, user_id: int, is_ready: bool) -> RoomMember:
    get_room(db, room_id)
    member = RoomMemberRepo(db).get(room_id, user_id)
    if member is None:
        raise StoryForgeError("not a member of this room", status_code=403)
    try:
        member.is_ready = 1 if is_ready else 0
        db.commit()
        db.refresh(member)
    except Exception:
        db.rollback()
        raise
    return member


def set_character(db: Session, room_id: int, user_id: int, character_id: int) -> RoomMember:
    room = get_room(db, room_id)
    if room.status == "playing":
        raise StoryForgeError("cannot change character while playing", status_code=409)
    member = RoomMemberRepo(db).get(room_id, user_id)
    if member is None:
        raise StoryForgeError("not a member of this room", status_code=403)
    _validate_character(db, user_id, character_id)
    try:
        member.character_id = character_id
        db.commit()
        db.refresh(member)
    except Exception:
        db.rollback()
        raise
    return member


def set_presence(db: Session, room_id: int, user_id: int, online: bool) -> RoomMember | None:
    """WS 连接/断开时更新在线状态。找不到成员时静默返回 None。"""
    member = RoomMemberRepo(db).get(room_id, user_id)
    if member is None:
        return None
    try:
        RoomMemberRepo(db).set_online(member, online)
        db.commit()
        db.refresh(member)
    except Exception:
        db.rollback()
        raise
    return member

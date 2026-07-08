# -*- coding: utf-8 -*-
"""房间聊天 / 事件流服务 (docs/multiplayer-realtime-design §5 / §6)

room_messages 是房间事件流的持久层：玩家聊天、系统提示、AI 广播镜像都落这里，
按 seq 排序，支持断线重连分页补齐。与叙事日志 messages（单局剧情）解耦。
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from backend.app.models.models import RoomMessage
from backend.app.repositories.room_repository import RoomMessageRepo
from backend.app.schemas.room_schema import RoomMessageDTO


def message_dto(msg: RoomMessage) -> RoomMessageDTO:
    try:
        payload = json.loads(msg.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    return RoomMessageDTO(
        id=msg.id,
        room_id=msg.room_id,
        seq=msg.seq,
        sender_role=msg.sender_role,
        sender_user_id=msg.sender_user_id,
        sender_name=msg.sender_name,
        message_type=msg.message_type,
        content=msg.content,
        payload=payload,
        client_msg_id=msg.client_msg_id,
        created_at=msg.created_at,
    )


def persist_message(
    db: Session,
    *,
    room_id: int,
    sender_role: str,
    message_type: str,
    content: str,
    session_id: int | None = None,
    sender_user_id: int | None = None,
    sender_name: str | None = None,
    payload: dict | None = None,
    client_msg_id: str | None = None,
) -> RoomMessage:
    return RoomMessageRepo(db).create(
        room_id=room_id,
        sender_role=sender_role,
        message_type=message_type,
        content=content,
        session_id=session_id,
        sender_user_id=sender_user_id,
        sender_name=sender_name,
        payload_json=json.dumps(payload or {}, ensure_ascii=False),
        client_msg_id=client_msg_id,
    )


def post_chat(
    db: Session,
    *,
    room_id: int,
    user_id: int,
    sender_name: str | None,
    content: str,
    session_id: int | None = None,
    client_msg_id: str | None = None,
) -> tuple[RoomMessage, bool]:
    """写入一条玩家聊天。返回 (message, is_new)；重复 client_msg_id 时 is_new=False。"""
    repo = RoomMessageRepo(db)
    if client_msg_id:
        existing = repo.find_by_client_id(room_id, client_msg_id)
        if existing is not None:
            return existing, False
    try:
        msg = repo.create(
            room_id=room_id,
            sender_role="user",
            message_type="chat",
            content=content,
            session_id=session_id,
            sender_user_id=user_id,
            sender_name=sender_name,
            client_msg_id=client_msg_id,
        )
        db.commit()
        db.refresh(msg)
    except Exception:
        db.rollback()
        raise
    return msg, True


def post_ooc(
    db: Session,
    *,
    room_id: int,
    user_id: int,
    sender_name: str | None,
    content: str,
    session_id: int | None = None,
    client_msg_id: str | None = None,
) -> tuple[RoomMessage, bool]:
    """写入一条 OOC（场外）聊天。返回 (message, is_new)。"""
    repo = RoomMessageRepo(db)
    if client_msg_id:
        existing = repo.find_by_client_id(room_id, client_msg_id)
        if existing is not None:
            return existing, False
    try:
        msg = repo.create(
            room_id=room_id,
            sender_role="user",
            message_type="ooc",
            content=content,
            session_id=session_id,
            sender_user_id=user_id,
            sender_name=sender_name,
            client_msg_id=client_msg_id,
        )
        db.commit()
        db.refresh(msg)
    except Exception:
        db.rollback()
        raise
    return msg, True


def list_history(
    db: Session,
    room_id: int,
    *,
    viewer_user_id: int | None = None,
    before_seq: int | None = None,
    after_seq: int | None = None,
    limit: int = 50,
) -> list[RoomMessageDTO]:
    rows = RoomMessageRepo(db).list_page(
        room_id, before_seq=before_seq, after_seq=after_seq, limit=limit
    )
    out: list[RoomMessageDTO] = []
    for row in rows:
        dto = message_dto(row)
        if viewer_user_id is not None and _is_private_to_other(dto, viewer_user_id):
            continue
        out.append(dto)
    return out


def _is_private_to_other(dto: RoomMessageDTO, viewer_user_id: int) -> bool:
    if dto.message_type not in ("guidance", "dm_ask"):
        return False
    vis = (dto.payload or {}).get("visibility", "self")
    if vis != "self":
        return False
    target = (dto.payload or {}).get("target_user_id")
    if target is not None:
        return target != viewer_user_id
    if dto.message_type == "dm_ask" and dto.sender_user_id is not None:
        return dto.sender_user_id != viewer_user_id
    return False

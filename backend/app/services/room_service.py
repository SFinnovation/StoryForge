# -*- coding: utf-8 -*-
"""房间生命周期服务 (docs/multiplayer-realtime-design §6)

职责：建房 / 查询 / 房间快照 / 开局（host）/ 结束。成员进出见 room_member_service，
聊天见 chat_service，行动见 room_action_service。
"""
from __future__ import annotations

import secrets
import string
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.core.exceptions import StoryForgeError
from backend.app.models.models import Character, GameSession, Room, RoomMember, User, World
from backend.app.repositories.room_repository import (
    RoomMemberRepo,
    RoomMessageRepo,
    RoomRepo,
)
from backend.app.schemas.room_schema import (
    RoomCreateRequest,
    RoomDetailDTO,
    RoomDTO,
    RoomMemberDTO,
)
from backend.app.services.ai_service import get_ai_service
from backend.app.services.context_builder import build_for_opening
from backend.app.services.state_committer import commit_opening
from backend.app.services.websocket_manager import connection_manager
from backend.app.services.world_seed import seed_session_world_data

_CODE_ALPHABET = string.ascii_uppercase + string.digits


def _generate_room_code(db: Session) -> str:
    for _ in range(20):
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
        if RoomRepo(db).get_by_code(code) is None:
            return code
    raise StoryForgeError("failed to allocate room code", status_code=500)


# ---------------- DTO 转换 ----------------


def room_dto(room: Room) -> RoomDTO:
    return RoomDTO(
        id=room.id,
        room_code=room.room_code,
        title=room.title,
        description=room.description,
        world_id=room.world_id,
        owner_id=room.owner_id,
        current_session_id=room.current_session_id,
        visibility=room.visibility,
        status=room.status,
        max_players=room.max_players,
        created_at=room.created_at,
    )


def member_dto(member: RoomMember) -> RoomMemberDTO:
    return RoomMemberDTO(
        user_id=member.user_id,
        character_id=member.character_id,
        role=member.role,
        display_name=member.display_name,
        online_status=member.online_status,
        is_ready=bool(member.is_ready),
    )


def detail_dto(db: Session, room: Room) -> RoomDetailDTO:
    members = RoomMemberRepo(db).list_by_room(room.id)
    online = connection_manager.online_user_ids(room.id)
    dtos: list[RoomMemberDTO] = []
    for m in members:
        dto = member_dto(m)
        if m.user_id in online:
            dto.online_status = "online"
        dtos.append(dto)
    return RoomDetailDTO(room=room_dto(room), members=dtos)


# ---------------- 查询与校验 ----------------


def get_room(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise StoryForgeError("room not found", status_code=404)
    return room


def require_member(db: Session, room_id: int, user_id: int) -> RoomMember:
    member = RoomMemberRepo(db).get(room_id, user_id)
    if member is None:
        raise StoryForgeError("not a member of this room", status_code=403)
    return member


def require_owner(db: Session, room_id: int, user_id: int) -> Room:
    room = get_room(db, room_id)
    if room.owner_id != user_id:
        raise StoryForgeError("only room owner can perform this action", status_code=403)
    return room


def list_my_rooms(db: Session, user_id: int) -> list[RoomDTO]:
    return [room_dto(r) for r in RoomRepo(db).list_for_user(user_id)]


def list_public_rooms(db: Session) -> list[RoomDTO]:
    return [room_dto(r) for r in RoomRepo(db).list_public()]


# ---------------- 建房 ----------------


def create_room(db: Session, user_id: int, payload: RoomCreateRequest) -> RoomDetailDTO:
    world = db.get(World, payload.world_id)
    if world is None or not world.is_enabled:
        raise StoryForgeError("world not found", status_code=404)
    user = db.get(User, user_id)

    try:
        room = RoomRepo(db).create(
            room_code=_generate_room_code(db),
            title=payload.title,
            world_id=payload.world_id,
            owner_id=user_id,
            description=payload.description,
            visibility=payload.visibility,
            max_players=payload.max_players,
        )
        RoomMemberRepo(db).add(
            room_id=room.id,
            user_id=user_id,
            role="host",
            display_name=(user.nickname or user.username) if user else None,
        )
        db.commit()
        db.refresh(room)
    except Exception:
        db.rollback()
        raise
    return detail_dto(db, room)


def get_room_detail(db: Session, room_id: int, user_id: int) -> RoomDetailDTO:
    room = get_room(db, room_id)
    require_member(db, room_id, user_id)
    return detail_dto(db, room)


# ---------------- 开局（host）----------------


async def start_game(
    db: Session,
    room_id: int,
    user_id: int,
    character_id: int | None = None,
) -> dict:
    """host 开局：建 multiplayer 会话 + AI 开局 + 灌入模组数据，房间转 playing。

    返回 dict：{"detail": RoomDetailDTO, "opening": OpeningOutput, "opening_message": Message}
    供路由/WS 落库房间事件并广播。
    """
    room = require_owner(db, room_id, user_id)
    if room.status == "playing" and room.current_session_id:
        raise StoryForgeError("room is already playing", status_code=409)

    host_member = require_member(db, room_id, user_id)
    chosen_character_id = character_id or host_member.character_id
    if chosen_character_id is None:
        raise StoryForgeError("host must select a character before starting", status_code=422)

    character = db.get(Character, chosen_character_id)
    if character is None or character.user_id != user_id:
        raise StoryForgeError("character not found", status_code=404)
    world = db.get(World, room.world_id)
    if world is None or not world.is_enabled:
        raise StoryForgeError("world not found", status_code=404)

    try:
        session = GameSession(
            user_id=user_id,
            world_id=world.id,
            character_id=character.id,
            title=room.title,
            status="playing",
            mode="multiplayer",
            host_user_id=user_id,
            room_id=room.id,
            started_at=datetime.utcnow(),
        )
        db.add(session)
        db.flush()

        ai = get_ai_service()
        opening_input = build_for_opening(db, world, character)
        opening_result = await ai.generate_opening(opening_input)
        opening = opening_result.output

        opening_message = commit_opening(
            db,
            session,
            narration=opening.display_text,
            scene_title=opening.scene_title,
            main_task=opening.main_task,
            tokens_used=opening_result.tokens_used,
            latency_ms=opening_result.latency_ms,
        )
        seed_session_world_data(db, session.id, world, opening)

        if host_member.character_id is None:
            host_member.character_id = character.id
        room.status = "playing"
        room.current_session_id = session.id
        RoomRepo(db).touch(room)
        db.commit()
        db.refresh(room)
    except StoryForgeError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    return {
        "detail": detail_dto(db, room),
        "session_id": session.id,
        "opening": opening,
        "opening_message": opening_message,
    }


def end_game(db: Session, room_id: int, user_id: int) -> RoomDetailDTO:
    room = require_owner(db, room_id, user_id)
    try:
        if room.current_session_id:
            session = db.get(GameSession, room.current_session_id)
            if session is not None and session.status == "playing":
                session.status = "finished"
                session.ended_at = datetime.utcnow()
        room.status = "finished"
        RoomRepo(db).touch(room)
        db.commit()
        db.refresh(room)
    except Exception:
        db.rollback()
        raise
    return detail_dto(db, room)

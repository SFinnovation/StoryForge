# -*- coding: utf-8 -*-
"""房间 REST 接口 (docs/multiplayer-realtime-design §4)

实时事件主通道是 WebSocket（见 ws_rooms.py），这里的 REST 提供建房/查询/成员管理，
并为聊天与行动提供“可直接测试”的 HTTP 回退——处理成功后同样向房间广播事件。
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_id, get_db_session
from backend.app.schemas.api_response import success
from backend.app.schemas.room_schema import (
    RoomActionRequest,
    RoomAskRequest,
    RoomChatRequest,
    RoomOocRequest,
    RoomCharacterRequest,
    RoomCreateRequest,
    RoomJoinRequest,
    RoomReadyRequest,
    RoomStartRequest,
)
from backend.app.services import (
    chat_service,
    guidance_service,
    room_action_service,
    room_member_service,
    room_service,
)
from backend.app.services.realtime_service import make_event
from backend.app.services.websocket_manager import connection_manager

router = APIRouter(prefix="/rooms", tags=["rooms"])


async def _broadcast_snapshot(db: Session, room_id: int) -> None:
    room = room_service.get_room(db, room_id)
    detail = room_service.detail_dto(db, room)
    await connection_manager.broadcast(
        room_id, make_event("room.updated", room_id, detail.model_dump())
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreateRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    detail = room_service.create_room(db, user_id, payload)
    return success(detail.model_dump(), message="room created")


@router.get("")
def list_rooms(
    scope: str = Query(default="mine", pattern="^(mine|public)$"),
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    if scope == "public":
        rows = room_service.list_public_rooms(db)
    else:
        rows = room_service.list_my_rooms(db, user_id)
    return success([r.model_dump() for r in rows])


@router.post("/join")
async def join_room(
    payload: RoomJoinRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    room_id, member, is_new = room_member_service.join_room(db, user_id, payload)
    if is_new:
        await connection_manager.broadcast(
            room_id,
            make_event(
                "member.joined",
                room_id,
                room_service.member_dto(member).model_dump(),
            ),
        )
        await _broadcast_snapshot(db, room_id)
    detail = room_service.get_room_detail(db, room_id, user_id)
    return success(detail.model_dump())


@router.get("/{room_id}")
def get_room(
    room_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    return success(room_service.get_room_detail(db, room_id, user_id).model_dump())


@router.post("/{room_id}/leave")
async def leave_room(
    room_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    result = room_member_service.leave_room(db, room_id, user_id)
    if result["removed"]:
        await connection_manager.broadcast(
            room_id, make_event("member.left", room_id, {"user_id": user_id})
        )
        await _broadcast_snapshot(db, room_id)
    return success(result)


@router.post("/{room_id}/ready")
async def set_ready(
    room_id: int,
    payload: RoomReadyRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    room_member_service.set_ready(db, room_id, user_id, payload.is_ready)
    await _broadcast_snapshot(db, room_id)
    return success({"is_ready": payload.is_ready})


@router.post("/{room_id}/character")
async def set_character(
    room_id: int,
    payload: RoomCharacterRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    room_member_service.set_character(db, room_id, user_id, payload.character_id)
    await _broadcast_snapshot(db, room_id)
    return success({"character_id": payload.character_id})


@router.post("/{room_id}/start")
async def start_game(
    room_id: int,
    payload: RoomStartRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    result = await room_service.start_game(db, room_id, user_id, payload.character_id)
    opening = result["opening"]
    session_id = result["session_id"]

    opening_msg = chat_service.persist_message(
        db,
        room_id=room_id,
        sender_role="ai_dm",
        message_type="narration",
        content=opening.display_text,
        session_id=session_id,
        sender_name="AI DM",
        payload={
            "scene_title": opening.scene_title,
            "main_task": opening.main_task,
            "initial_clues": [c.model_dump() if hasattr(c, "model_dump") else c
                              for c in opening.initial_clues],
            "npcs": [n.model_dump() if hasattr(n, "model_dump") else n for n in opening.npcs],
        },
    )
    db.commit()
    db.refresh(opening_msg)

    await connection_manager.broadcast(
        room_id,
        make_event("game.started", room_id, result["detail"].model_dump()),
    )
    await connection_manager.broadcast(
        room_id,
        make_event(
            "dm.narration", room_id,
            chat_service.message_dto(opening_msg).model_dump(),
            seq=opening_msg.seq,
        ),
    )
    return success(
        {
            "detail": result["detail"].model_dump(),
            "session_id": session_id,
            "opening_message": chat_service.message_dto(opening_msg).model_dump(),
        }
    )


@router.post("/{room_id}/end")
async def end_game(
    room_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    detail = room_service.end_game(db, room_id, user_id)
    await connection_manager.broadcast(
        room_id, make_event("game.ended", room_id, detail.model_dump())
    )
    return success(detail.model_dump())


@router.get("/{room_id}/messages")
def list_messages(
    room_id: int,
    before_seq: int | None = Query(default=None),
    after_seq: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    room_service.require_member(db, room_id, user_id)
    rows = chat_service.list_history(
        db, room_id, viewer_user_id=user_id,
        before_seq=before_seq, after_seq=after_seq, limit=limit,
    )
    return success([m.model_dump() for m in rows])


@router.post("/{room_id}/chat")
async def post_chat(
    room_id: int,
    payload: RoomChatRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    member = room_service.require_member(db, room_id, user_id)
    room = room_service.get_room(db, room_id)
    msg, is_new = chat_service.post_chat(
        db,
        room_id=room_id,
        user_id=user_id,
        sender_name=member.display_name,
        content=payload.content,
        session_id=room.current_session_id,
        client_msg_id=payload.client_msg_id,
    )
    dto = chat_service.message_dto(msg)
    if is_new:
        await connection_manager.broadcast(
            room_id, make_event("chat.message", room_id, dto.model_dump(), seq=msg.seq)
        )
    return success(dto.model_dump())


@router.post("/{room_id}/ooc")
async def post_ooc(
    room_id: int,
    payload: RoomOocRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    member = room_service.require_member(db, room_id, user_id)
    room = room_service.get_room(db, room_id)
    msg, is_new = chat_service.post_ooc(
        db,
        room_id=room_id,
        user_id=user_id,
        sender_name=member.display_name,
        content=payload.content,
        session_id=room.current_session_id,
        client_msg_id=payload.client_msg_id,
    )
    dto = chat_service.message_dto(msg)
    if is_new:
        await connection_manager.broadcast(
            room_id, make_event("ooc.message", room_id, dto.model_dump(), seq=msg.seq)
        )
    return success(dto.model_dump())


@router.post("/{room_id}/ask")
async def ask_dm(
    room_id: int,
    payload: RoomAskRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    member = room_service.require_member(db, room_id, user_id)
    result = await guidance_service.handle_dm_ask(
        db,
        room_id,
        user_id,
        payload.question,
        sender_name=member.display_name,
        client_msg_id=payload.client_msg_id,
        visibility=payload.visibility,
    )
    await guidance_service.dispatch_dm_ask_events(room_id, user_id, result)
    reply = result.get("reply_message")
    return success(
        {
            "duplicate": result.get("duplicate", False),
            "reply": chat_service.message_dto(reply).model_dump() if reply else None,
        }
    )


@router.post("/{room_id}/action")
async def submit_action(
    room_id: int,
    payload: RoomActionRequest,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    result = await room_action_service.handle_action(
        db, room_id, user_id, payload.action_text, client_msg_id=payload.client_msg_id
    )
    for event in result["events"]:
        await connection_manager.broadcast(room_id, event)
    action_data = result["action_data"]
    return success(
        {
            "duplicate": result["duplicate"],
            "action_data": action_data.model_dump() if action_data else None,
        }
    )

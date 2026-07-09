# -*- coding: utf-8 -*-
"""房间 WebSocket 实时通道 (docs/multiplayer-realtime-design §5)

路径：/api/v1/ws/rooms/{room_id}?token=<access_token>
浏览器 WebSocket 无法自定义 Header，故 token 走查询参数。

客户端→服务端事件：
  chat.send     {data:{content, client_msg_id}}
  ooc.send      {data:{content, client_msg_id}}
  action.submit {data:{action_text, client_msg_id}}
  dm.ask        {data:{question, client_msg_id, visibility?}}
  typing.start  {}
  typing.stop   {}
  ping          {}
服务端→客户端事件：见 realtime_service.make_event / rooms.py 广播。
"""
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.api.deps import DEMO_USER_ID
from backend.app.core.exceptions import StoryForgeError
from backend.app.db.database import SessionLocal
from backend.app.repositories.room_repository import RoomMemberRepo
from backend.app.services import chat_service, guidance_service, room_action_service, room_member_service, room_service
from backend.app.services.auth_service import decode_access_token
from backend.app.services.realtime_service import make_event
from backend.app.services.websocket_manager import connection_manager

router = APIRouter(tags=["rooms-ws"])

WS_CLOSE_UNAUTHORIZED = 4401
WS_CLOSE_FORBIDDEN = 4403


def _authenticate(token: str | None) -> int | None:
    if not token:
        return DEMO_USER_ID
    try:
        return decode_access_token(token).user_id
    except StoryForgeError:
        return None


async def _send_initial_snapshot(websocket: WebSocket, room_id: int, user_id: int) -> None:
    with SessionLocal() as db:
        room = room_service.get_room(db, room_id)
        detail = room_service.detail_dto(db, room)
        history = chat_service.list_history(db, room_id, viewer_user_id=user_id, limit=50)
    await connection_manager.send(
        websocket,
        make_event(
            "room.snapshot",
            room_id,
            {
                "room": detail.room.model_dump(),
                "members": [m.model_dump() for m in detail.members],
                "messages": [m.model_dump() for m in history],
            },
        ),
    )


@router.websocket("/ws/rooms/{room_id}")
async def room_socket(
    websocket: WebSocket,
    room_id: int,
    token: str | None = Query(default=None),
):
    user_id = _authenticate(token)
    if user_id is None:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return

    # 成员校验
    with SessionLocal() as db:
        member = RoomMemberRepo(db).get(room_id, user_id)
        display_name = member.display_name if member else None
    if member is None:
        await websocket.close(code=WS_CLOSE_FORBIDDEN)
        return

    await connection_manager.connect(room_id, user_id, websocket)

    with SessionLocal() as db:
        room_member_service.set_presence(db, room_id, user_id, True)
    await _send_initial_snapshot(websocket, room_id, user_id)
    await connection_manager.broadcast(
        room_id,
        make_event(
            "member.presence", room_id,
            {"user_id": user_id, "online_status": "online"},
        ),
        exclude=websocket,
    )
    await connection_manager.broadcast(
        room_id,
        make_event("member.online", room_id, {"user_id": user_id}),
        exclude=websocket,
    )

    try:
        while True:
            raw = await websocket.receive_json()
            await _dispatch(websocket, room_id, user_id, display_name, raw)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        connection_manager.disconnect(room_id, websocket)
        still_online = connection_manager.has_other_connection(room_id, user_id, websocket)
        if not still_online:
            with SessionLocal() as db:
                room_member_service.set_presence(db, room_id, user_id, False)
            await connection_manager.broadcast(
                room_id,
                make_event(
                    "member.presence", room_id,
                    {"user_id": user_id, "online_status": "offline"},
                ),
            )
            await connection_manager.broadcast(
                room_id,
                make_event("member.offline", room_id, {"user_id": user_id}),
            )


async def _dispatch(
    websocket: WebSocket,
    room_id: int,
    user_id: int,
    display_name: str | None,
    raw: dict,
) -> None:
    event_type = (raw or {}).get("type")
    data = (raw or {}).get("data") or {}

    if event_type == "ping":
        await connection_manager.send(websocket, make_event("pong", room_id, {}))
        return

    if event_type == "chat.send":
        content = str(data.get("content") or "").strip()
        if not content:
            return
        with SessionLocal() as db:
            room = room_service.get_room(db, room_id)
            msg, is_new = chat_service.post_chat(
                db,
                room_id=room_id,
                user_id=user_id,
                sender_name=display_name,
                content=content,
                session_id=room.current_session_id,
                client_msg_id=data.get("client_msg_id"),
            )
            dto = chat_service.message_dto(msg)
        if is_new:
            await connection_manager.broadcast(
                room_id, make_event("chat.message", room_id, dto.model_dump(), seq=msg.seq)
            )
        return

    if event_type == "ooc.send":
        content = str(data.get("content") or "").strip()
        if not content:
            return
        with SessionLocal() as db:
            room = room_service.get_room(db, room_id)
            msg, is_new = chat_service.post_ooc(
                db,
                room_id=room_id,
                user_id=user_id,
                sender_name=display_name,
                content=content,
                session_id=room.current_session_id,
                client_msg_id=data.get("client_msg_id"),
            )
            dto = chat_service.message_dto(msg)
        if is_new:
            await connection_manager.broadcast(
                room_id, make_event("ooc.message", room_id, dto.model_dump(), seq=msg.seq)
            )
        return

    if event_type == "action.submit":
        action_text = str(data.get("action_text") or "").strip()
        if not action_text:
            return
        with SessionLocal() as db:
            try:
                result = await room_action_service.handle_action(
                    db, room_id, user_id, action_text,
                    client_msg_id=data.get("client_msg_id"),
                )
            except StoryForgeError as exc:
                await connection_manager.send(
                    websocket, make_event("error", room_id, {"message": exc.message})
                )
                return
            except Exception as exc:
                await connection_manager.send(
                    websocket,
                    make_event("error", room_id, {"message": f"action failed: {exc}"}),
                )
                return
        for event in result["events"]:
            await connection_manager.broadcast(room_id, event)
        return

    if event_type == "dm.ask":
        question = str(data.get("question") or "").strip()
        if not question:
            return
        with SessionLocal() as db:
            try:
                result = await guidance_service.handle_dm_ask(
                    db,
                    room_id,
                    user_id,
                    question,
                    sender_name=display_name,
                    client_msg_id=data.get("client_msg_id"),
                    visibility=str(data.get("visibility") or "self"),
                )
            except StoryForgeError as exc:
                await connection_manager.send(
                    websocket, make_event("error", room_id, {"message": exc.message})
                )
                return
            except Exception as exc:
                await connection_manager.send(
                    websocket,
                    make_event("error", room_id, {"message": f"dm ask failed: {exc}"}),
                )
                return
        await guidance_service.dispatch_dm_ask_events(room_id, user_id, result)
        return

    if event_type in ("typing.start", "typing.stop"):
        await connection_manager.broadcast(
            room_id,
            make_event(
                event_type,
                room_id,
                {"user_id": user_id, "display_name": display_name},
            ),
            exclude=websocket,
        )
        return

    await connection_manager.send(
        websocket, make_event("error", room_id, {"message": f"unknown event: {event_type}"})
    )

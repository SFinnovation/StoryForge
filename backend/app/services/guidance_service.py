# -*- coding: utf-8 -*-
"""dm.ask / GuidanceAgent 编排 (multiplayer-realtime-design §6.5)

向 AI DM 提问规则与策略建议：不推进剧情、不写叙事 messages，仅落 room_messages。
默认仅向提问者推送回答（visibility=self）；visibility=room 时全房可见。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.core.exceptions import StoryForgeError
from backend.app.models.models import Character, GameSession
from backend.app.repositories.room_repository import RoomMessageRepo
from backend.app.services.ai_service import get_ai_service
from backend.app.services.chat_service import message_dto, persist_message
from backend.app.services.realtime_service import make_event
from backend.app.services.room_context_builder import build_for_guidance
from backend.app.services.room_service import get_room, require_member
from backend.app.services.websocket_manager import connection_manager


async def handle_dm_ask(
    db: Session,
    room_id: int,
    user_id: int,
    question: str,
    *,
    sender_name: str | None = None,
    client_msg_id: str | None = None,
    visibility: str = "self",
) -> dict:
    """返回 {events: list[dict], ask_message, reply_message}。"""
    room = get_room(db, room_id)
    member = require_member(db, room_id, user_id)
    text = (question or "").strip()
    if not text:
        raise StoryForgeError("question is required", status_code=422)
    if len(text) > 2000:
        raise StoryForgeError("question too long", status_code=422)

    actor_name = sender_name or member.display_name or f"user_{user_id}"
    session: GameSession | None = None
    character: Character | None = None
    if member.character_id:
        character = db.get(Character, member.character_id)
    if room.current_session_id:
        session = db.get(GameSession, room.current_session_id)

    repo = RoomMessageRepo(db)
    if client_msg_id:
        existing = repo.find_by_client_id(room_id, client_msg_id)
        if existing is not None:
            return {"duplicate": True, "events": [], "ask_message": existing, "reply_message": None}

    await connection_manager.broadcast(
        room_id,
        make_event("ai.thinking", room_id, {"stage": "guidance"}, actor={"user_id": user_id}),
    )

    guidance_in = build_for_guidance(db, room, member, session, character)
    guidance_in.question = text

    result = await get_ai_service().generate_guidance(guidance_in)
    output = result.output

    try:
        ask_msg = persist_message(
            db,
            room_id=room_id,
            sender_role="user",
            message_type="dm_ask",
            content=text,
            session_id=room.current_session_id,
            sender_user_id=user_id,
            sender_name=actor_name,
            payload={"visibility": visibility, "target_user_id": user_id},
            client_msg_id=client_msg_id,
        )
        reply_msg = persist_message(
            db,
            room_id=room_id,
            sender_role="ai_dm",
            message_type="guidance",
            content=output.answer,
            session_id=room.current_session_id,
            sender_name="AI DM",
            payload={
                "suggested_options": output.suggested_options,
                "rule_hint": output.rule_hint,
                "question": text,
                "target_user_id": user_id,
                "visibility": visibility,
                "tokens_used": result.tokens_used,
            },
        )
        db.commit()
        db.refresh(ask_msg)
        db.refresh(reply_msg)
    except Exception:
        db.rollback()
        raise

    ask_dto = message_dto(ask_msg).model_dump()
    reply_dto = message_dto(reply_msg).model_dump()
    events = [
        make_event("chat.message", room_id, ask_dto, seq=ask_msg.seq),
        make_event("dm.guidance", room_id, reply_dto, seq=reply_msg.seq),
    ]
    return {
        "duplicate": False,
        "events": events,
        "ask_message": ask_msg,
        "reply_message": reply_msg,
        "visibility": visibility,
        "target_user_id": user_id,
    }


async def dispatch_dm_ask_events(room_id: int, user_id: int, result: dict) -> None:
    """按 visibility 广播或定向发送 dm.ask 相关事件。"""
    if result.get("duplicate"):
        return
    visibility = result.get("visibility", "self")
    target = result.get("target_user_id", user_id)
    for event in result.get("events", []):
        if visibility == "room":
            await connection_manager.broadcast(room_id, event)
        else:
            await connection_manager.send_to_user(room_id, target, event)

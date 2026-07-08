# -*- coding: utf-8 -*-
"""多人行动编排 (docs/multiplayer-realtime-design §6.3 / §6.4)

一次玩家行动的完整链路：
  房间锁 → 幂等校验 → 记录 RoomAction → 复用单人行动管线（按行动者角色检定/叙事）
  → 将行动/骰子/AI 旁白镜像进 room_messages → 产出可广播事件（带 seq）。

房间级 asyncio.Lock 保证同一房间的行动串行处理，避免并发叙事/落库交错。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.core.exceptions import StoryForgeError
from backend.app.models.models import Character, GameSession
from backend.app.repositories.room_repository import RoomActionRepo, RoomMessageRepo
from backend.app.services.action_service import run_action_pipeline
from backend.app.services.chat_service import message_dto, persist_message
from backend.app.services.realtime_service import make_event
from backend.app.services.room_service import get_room, require_member
from backend.app.services.websocket_manager import connection_manager, get_room_lock


async def _broadcast_thinking(
    room_id: int, stage: str, *, actor: dict | None = None
) -> None:
    await connection_manager.broadcast(
        room_id, make_event("ai.thinking", room_id, {"stage": stage}, actor=actor)
    )


def _playing_session(db: Session, room) -> GameSession:
    if room.status != "playing" or not room.current_session_id:
        raise StoryForgeError("game not started", status_code=409)
    session = db.get(GameSession, room.current_session_id)
    if session is None or session.status != "playing":
        raise StoryForgeError("session is not playing", status_code=409)
    return session


async def handle_action(
    db: Session,
    room_id: int,
    user_id: int,
    action_text: str,
    *,
    client_msg_id: str | None = None,
) -> dict:
    """返回 {"duplicate": bool, "action_data": ActionData|None, "events": [dict]}。"""
    room = get_room(db, room_id)
    member = require_member(db, room_id, user_id)
    session = _playing_session(db, room)

    lock = get_room_lock(room_id)
    async with lock:
        messages = RoomMessageRepo(db)
        if client_msg_id and messages.find_by_client_id(room_id, client_msg_id) is not None:
            return {"duplicate": True, "action_data": None, "events": []}

        actor_char = (
            db.get(Character, member.character_id) if member.character_id else None
        )
        actor_name = member.display_name or (actor_char.name if actor_char else f"user_{user_id}")
        actor = {"user_id": user_id, "name": actor_name, "character_id": member.character_id}

        action_record = RoomActionRepo(db).create(
            room_id=room_id,
            session_id=session.id,
            actor_user_id=user_id,
            action_text=action_text,
            actor_character_id=member.character_id,
        )
        db.commit()

        await _broadcast_thinking(room_id, "parsing", actor=actor)

        try:
            await _broadcast_thinking(room_id, "narrating", actor=actor)
            data = await run_action_pipeline(
                db,
                session,
                action_text,
                actor_name=actor_name,
                character_override=actor_char,
            )
        except Exception:
            RoomActionRepo(db).mark(action_record, "rejected")
            db.commit()
            raise

        # ---- 镜像进 room_messages（一个事务内分配连续 seq）----
        try:
            m_action = persist_message(
                db,
                room_id=room_id,
                sender_role="user",
                message_type="action",
                content=action_text,
                session_id=session.id,
                sender_user_id=user_id,
                sender_name=actor_name,
                client_msg_id=client_msg_id,
            )
            m_dice = None
            if data.check is not None:
                m_dice = persist_message(
                    db,
                    room_id=room_id,
                    sender_role="system",
                    message_type="dice",
                    content=data.check.result_text,
                    session_id=session.id,
                    payload=data.check.model_dump(),
                )
            m_narration = persist_message(
                db,
                room_id=room_id,
                sender_role="ai_dm",
                message_type="narration",
                content=data.story.narration,
                session_id=session.id,
                sender_name="AI DM",
                payload={
                    "visible_result": data.story.visible_result,
                    "new_clues": data.story.new_clues,
                    "task_updates": data.story.task_updates,
                    "next_options": data.story.next_options,
                },
            )
            RoomActionRepo(db).mark(action_record, "done", result_message_id=m_narration.id)
            db.commit()
        except Exception:
            db.rollback()
            raise

        events = [
            make_event(
                "action.accepted",
                room_id,
                {"action_text": action_text, "client_msg_id": client_msg_id},
                actor=actor,
            ),
            make_event(
                "action.received", room_id, message_dto(m_action).model_dump(),
                seq=m_action.seq, actor=actor,
            )
        ]
        if m_dice is not None:
            dice_payload = message_dto(m_dice).model_dump()
            events.append(
                make_event("dice.result", room_id, dice_payload, seq=m_dice.seq)
            )
            events.append(
                make_event("dice.rolled", room_id, dice_payload, seq=m_dice.seq)
            )
        events.append(
            make_event(
                "dm.narration", room_id, message_dto(m_narration).model_dump(),
                seq=m_narration.seq,
            )
        )
        events.append(
            make_event(
                "ai.narration", room_id, message_dto(m_narration).model_dump(),
                seq=m_narration.seq,
            )
        )
        events.append(
            make_event(
                "state.updated",
                room_id,
                {
                    "session_meta": data.session_meta.model_dump(),
                    "ai_review": data.ai_review.model_dump(),
                },
            )
        )
        return {"duplicate": False, "action_data": data, "events": events}

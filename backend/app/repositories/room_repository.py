# -*- coding: utf-8 -*-
"""房间相关 Repository (docs/multiplayer-realtime-design §3 / §7)

四个表各一个 Repo, 复用 BaseRepo 的事务约定:
- Repo 只 add/flush, 不 commit; 事务边界由 service 控制。
- RoomMessageRepo.next_seq 在房间锁保护下调用, 保证 seq 单调递增。
"""
from datetime import datetime

from sqlalchemy import func

from backend.app.models.models import Room, RoomAction, RoomMember, RoomMessage
from backend.app.repositories.base import BaseRepo


class RoomRepo(BaseRepo):
    def create(
        self,
        *,
        room_code: str,
        title: str,
        world_id: int,
        owner_id: int,
        description: str | None = None,
        visibility: str = "private",
        max_players: int = 6,
    ) -> Room:
        room = Room(
            room_code=room_code,
            title=title,
            description=description,
            world_id=world_id,
            owner_id=owner_id,
            visibility=visibility,
            max_players=max_players,
            status="waiting",
        )
        self.db.add(room)
        self.db.flush()
        return room

    def get(self, room_id: int) -> Room | None:
        return self.db.get(Room, room_id)

    def get_by_code(self, room_code: str) -> Room | None:
        return (
            self.db.query(Room)
            .filter(Room.room_code == room_code)
            .first()
        )

    def list_for_user(self, user_id: int) -> list[Room]:
        """用户参与的所有房间（作为成员）。"""
        return (
            self.db.query(Room)
            .join(RoomMember, RoomMember.room_id == Room.id)
            .filter(RoomMember.user_id == user_id)
            .order_by(Room.updated_at.desc())
            .all()
        )

    def list_public(self) -> list[Room]:
        return (
            self.db.query(Room)
            .filter(
                Room.visibility == "public",
                Room.status.in_(("waiting", "playing", "paused")),
            )
            .order_by(Room.updated_at.desc())
            .all()
        )

    def touch(self, room: Room) -> None:
        room.updated_at = datetime.utcnow()


class RoomMemberRepo(BaseRepo):
    def add(
        self,
        *,
        room_id: int,
        user_id: int,
        role: str = "player",
        display_name: str | None = None,
        character_id: int | None = None,
    ) -> RoomMember:
        member = RoomMember(
            room_id=room_id,
            user_id=user_id,
            role=role,
            display_name=display_name,
            character_id=character_id,
            online_status="offline",
            is_ready=0,
        )
        self.db.add(member)
        self.db.flush()
        return member

    def get(self, room_id: int, user_id: int) -> RoomMember | None:
        return (
            self.db.query(RoomMember)
            .filter(RoomMember.room_id == room_id, RoomMember.user_id == user_id)
            .first()
        )

    def list_by_room(self, room_id: int) -> list[RoomMember]:
        return (
            self.db.query(RoomMember)
            .filter(RoomMember.room_id == room_id)
            .order_by(RoomMember.id.asc())
            .all()
        )

    def count(self, room_id: int) -> int:
        return (
            self.db.query(func.count(RoomMember.id))
            .filter(RoomMember.room_id == room_id)
            .scalar()
            or 0
        )

    def set_online(self, member: RoomMember, online: bool) -> None:
        member.online_status = "online" if online else "offline"
        member.last_seen_at = datetime.utcnow()


class RoomMessageRepo(BaseRepo):
    def next_seq(self, room_id: int) -> int:
        current = (
            self.db.query(func.max(RoomMessage.seq))
            .filter(RoomMessage.room_id == room_id)
            .scalar()
        )
        return int(current or 0) + 1

    def find_by_client_id(self, room_id: int, client_msg_id: str) -> RoomMessage | None:
        if not client_msg_id:
            return None
        return (
            self.db.query(RoomMessage)
            .filter(
                RoomMessage.room_id == room_id,
                RoomMessage.client_msg_id == client_msg_id,
            )
            .first()
        )

    def create(
        self,
        *,
        room_id: int,
        sender_role: str,
        message_type: str,
        content: str,
        session_id: int | None = None,
        sender_user_id: int | None = None,
        sender_name: str | None = None,
        payload_json: str = "{}",
        client_msg_id: str | None = None,
    ) -> RoomMessage:
        msg = RoomMessage(
            room_id=room_id,
            session_id=session_id,
            sender_user_id=sender_user_id,
            sender_role=sender_role,
            sender_name=sender_name,
            message_type=message_type,
            content=content,
            payload_json=payload_json,
            client_msg_id=client_msg_id,
            seq=self.next_seq(room_id),
        )
        self.db.add(msg)
        self.db.flush()
        return msg

    def list_page(
        self,
        room_id: int,
        *,
        before_seq: int | None = None,
        after_seq: int | None = None,
        limit: int = 50,
    ) -> list[RoomMessage]:
        """分页查询。before_seq：取更早一页；after_seq：断线重连补 seq 之后的消息。"""
        if after_seq is not None:
            rows = (
                self.db.query(RoomMessage)
                .filter(RoomMessage.room_id == room_id, RoomMessage.seq > after_seq)
                .order_by(RoomMessage.seq.asc())
                .limit(limit)
                .all()
            )
            return rows

        query = self.db.query(RoomMessage).filter(RoomMessage.room_id == room_id)
        if before_seq is not None:
            query = query.filter(RoomMessage.seq < before_seq)
        rows = query.order_by(RoomMessage.seq.desc()).limit(limit).all()
        return list(reversed(rows))


class RoomActionRepo(BaseRepo):
    def create(
        self,
        *,
        room_id: int,
        session_id: int | None,
        actor_user_id: int,
        action_text: str,
        actor_character_id: int | None = None,
    ) -> RoomAction:
        action = RoomAction(
            room_id=room_id,
            session_id=session_id,
            actor_user_id=actor_user_id,
            actor_character_id=actor_character_id,
            action_text=action_text,
            status="pending",
        )
        self.db.add(action)
        self.db.flush()
        return action

    def mark(
        self,
        action: RoomAction,
        status: str,
        *,
        result_message_id: int | None = None,
    ) -> None:
        action.status = status
        if result_message_id is not None:
            action.result_message_id = result_message_id
        if status in ("done", "rejected"):
            action.processed_at = datetime.utcnow()

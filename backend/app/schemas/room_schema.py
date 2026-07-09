# -*- coding: utf-8 -*-
"""房间相关 DTO (docs/multiplayer-realtime-design §4)"""
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------- 请求体 ----------------


class RoomCreateRequest(BaseModel):
    world_id: int
    title: str = Field(min_length=1, max_length=100)
    description: str | None = None
    visibility: str = "private"
    max_players: int = Field(default=6, ge=1, le=12)


class RoomJoinRequest(BaseModel):
    room_code: str = Field(min_length=1, max_length=12)
    character_id: int | None = None
    display_name: str | None = None


class RoomReadyRequest(BaseModel):
    is_ready: bool = True


class RoomCharacterRequest(BaseModel):
    character_id: int


class RoomStartRequest(BaseModel):
    character_id: int | None = None


class RoomChatRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    client_msg_id: str | None = None


class RoomOocRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    client_msg_id: str | None = None


class RoomActionRequest(BaseModel):
    action_text: str = Field(min_length=1, max_length=2000)
    client_msg_id: str | None = None


class RoomAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    client_msg_id: str | None = None
    visibility: str = Field(default="self", pattern="^(self|room)$")


# ---------------- 响应 DTO ----------------


class RoomMemberDTO(BaseModel):
    user_id: int
    character_id: int | None = None
    character_name: str | None = None
    role: str
    display_name: str | None = None
    online_status: str = "offline"
    is_ready: bool = False


class RoomDTO(BaseModel):
    id: int
    room_code: str
    title: str
    description: str | None = None
    world_id: int
    owner_id: int
    current_session_id: int | None = None
    visibility: str
    status: str
    max_players: int
    created_at: datetime | str | None = None


class RoomDetailDTO(BaseModel):
    room: RoomDTO
    members: list[RoomMemberDTO] = Field(default_factory=list)


class RoomMessageDTO(BaseModel):
    id: int
    room_id: int
    seq: int
    sender_role: str
    sender_user_id: int | None = None
    sender_name: str | None = None
    message_type: str
    content: str
    payload: dict = Field(default_factory=dict)
    client_msg_id: str | None = None
    created_at: datetime | str | None = None

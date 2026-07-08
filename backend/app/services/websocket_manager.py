# -*- coding: utf-8 -*-
"""WebSocket 连接管理与房间级并发锁 (docs/multiplayer-realtime-design §5 / §6.4)

- ConnectionManager 维护 room_id -> 连接集合, 负责注册/注销/广播。
- get_room_lock 提供房间级 asyncio.Lock, 保证同一房间的行动/开局串行处理,
  避免多个玩家同时提交行动时叙事/落库交错。
- 进程内单例; 多进程部署需换成 Redis pub/sub（见 §14 技术债）。
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import date, datetime

from starlette.websockets import WebSocket, WebSocketState


def _json_default(value: object) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _dumps_event(event: dict) -> str:
    return json.dumps(event, ensure_ascii=False, default=_json_default)


class ConnectionManager:
    def __init__(self) -> None:
        # room_id -> { websocket -> user_id }
        self._rooms: dict[int, dict[WebSocket, int]] = defaultdict(dict)

    async def connect(self, room_id: int, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms[room_id][websocket] = user_id

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        conns = self._rooms.get(room_id)
        if conns is not None:
            conns.pop(websocket, None)
            if not conns:
                self._rooms.pop(room_id, None)

    def online_user_ids(self, room_id: int) -> set[int]:
        return set(self._rooms.get(room_id, {}).values())

    def has_other_connection(self, room_id: int, user_id: int, exclude: WebSocket) -> bool:
        """该用户在本房间是否还有其它活跃连接（多标签页场景下判断真正离线）。"""
        for ws, uid in self._rooms.get(room_id, {}).items():
            if uid == user_id and ws is not exclude:
                return True
        return False

    async def broadcast(self, room_id: int, event: dict, *, exclude: WebSocket | None = None) -> None:
        conns = list(self._rooms.get(room_id, {}).keys())
        stale: list[WebSocket] = []
        for ws in conns:
            if ws is exclude:
                continue
            if ws.application_state != WebSocketState.CONNECTED:
                stale.append(ws)
                continue
            try:
                await ws.send_text(_dumps_event(event))
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(room_id, ws)

    async def send(self, websocket: WebSocket, event: dict) -> None:
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.send_text(_dumps_event(event))

    async def send_to_user(self, room_id: int, user_id: int, event: dict) -> None:
        for ws, uid in list(self._rooms.get(room_id, {}).items()):
            if uid != user_id:
                continue
            if ws.application_state != WebSocketState.CONNECTED:
                self.disconnect(room_id, ws)
                continue
            try:
                await ws.send_text(_dumps_event(event))
            except Exception:
                self.disconnect(room_id, ws)


connection_manager = ConnectionManager()

# 房间级串行锁
_room_locks: dict[int, asyncio.Lock] = {}


def get_room_lock(room_id: int) -> asyncio.Lock:
    lock = _room_locks.get(room_id)
    if lock is None:
        lock = asyncio.Lock()
        _room_locks[room_id] = lock
    return lock

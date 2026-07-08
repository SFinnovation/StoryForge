# -*- coding: utf-8 -*-
"""实时事件封装与广播 (docs/multiplayer-realtime-design §5.2 / §10.3)

约定：先落库（拿到 seq）再广播，保证断线重连能按 seq 补齐、且客户端可去重。
事件信封统一为 {v, type, room_id, seq, ts, actor, data}。
"""
from __future__ import annotations

from datetime import datetime

PROTOCOL_VERSION = 1


def make_event(
    event_type: str,
    room_id: int,
    data: dict,
    *,
    seq: int | None = None,
    actor: dict | None = None,
) -> dict:
    return {
        "v": PROTOCOL_VERSION,
        "type": event_type,
        "room_id": room_id,
        "seq": seq,
        "ts": datetime.utcnow().isoformat() + "Z",
        "actor": actor,
        "data": data,
    }

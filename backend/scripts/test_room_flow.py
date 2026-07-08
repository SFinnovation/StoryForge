# -*- coding: utf-8 -*-
"""多人房间 P0 冒烟测试（服务层，无需 LLM / 无需起服务）。

覆盖：建表 → 建房 → 第二名玩家加入 → 选角色 → host 开局(AI 走 fallback)
     → 玩家提交行动(检定/叙事/落库/事件) → 聊天 → 历史分页。

用法（PowerShell）：
    python backend/scripts/test_room_flow.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

os.environ["DATABASE_URL"] = "sqlite:///./test_room_flow.db"
os.environ.setdefault("AKP_ENABLED", "false")

from backend.app.db.database import SessionLocal
from backend.app.db.init_db import init_db
from backend.app.models.models import Character, RoomMessage, User, World
from backend.app.schemas.room_schema import (
    RoomCreateRequest,
    RoomJoinRequest,
)
from backend.app.services import (
    chat_service,
    guidance_service,
    room_action_service,
    room_member_service,
    room_service,
)


def _seed() -> tuple[int, int, int, int]:
    with SessionLocal() as db:
        host = User(username="host_alice", password_hash="demo", nickname="爱丽丝", role="user")
        guest = User(username="guest_bob", password_hash="demo", nickname="鲍勃", role="user")
        db.add_all([host, guest])
        db.flush()

        world = World(
            name="追捕克仑可（多人冒烟）", type="fantasy",
            description="锻炉街的鬼怪追捕", opening_prompt="Open a concise heist scene.",
            rule_style="lite_dnd", difficulty="normal", is_enabled=1, created_by=host.id,
        )
        db.add(world)
        db.flush()

        host_char = Character(
            user_id=host.id, name="凯尔·维恩", race_id="human", class_id="rogue",
            background_id="detective", motivation="追捕克仑可", level=1, hp=9, max_hp=9,
            strength=13, dexterity=15, constitution=12, intelligence=14, wisdom=10, charisma=8,
            skills_json='{"per": {"proficient": true}}', saving_throws_json='["dexterity"]',
        )
        guest_char = Character(
            user_id=guest.id, name="米拉·石心", race_id="dwarf", class_id="fighter",
            background_id="soldier", motivation="保护同伴", level=1, hp=12, max_hp=12,
            strength=15, dexterity=12, constitution=14, intelligence=8, wisdom=10, charisma=10,
            skills_json='{"ath": {"proficient": true}}', saving_throws_json='["strength"]',
        )
        db.add_all([host_char, guest_char])
        db.commit()
        return host.id, guest.id, host_char.id, guest_char.id


async def main() -> int:
    print("== 初始化数据库 ==")
    init_db(drop_first=True)
    host_id, guest_id, host_char_id, guest_char_id = _seed()
    print(f"host={host_id} guest={guest_id} host_char={host_char_id} guest_char={guest_char_id}")

    with SessionLocal() as db:
        world = db.query(World).first()
        # 1) 建房（host 自动成为 host 成员）
        detail = room_service.create_room(
            db, host_id,
            RoomCreateRequest(world_id=world.id, title="锻炉街突袭", max_players=4),
        )
        room_id = detail.room.id
        code = detail.room.room_code
        print(f"\n== 建房 room_id={room_id} code={code} 成员数={len(detail.members)} ==")
        assert len(detail.members) == 1 and detail.members[0].role == "host"

        # 2) host 选择角色
        room_member_service.set_character(db, room_id, host_id, host_char_id)

        # 3) 第二名玩家加入并选角色
        rid, member, is_new = room_member_service.join_room(
            db, guest_id, RoomJoinRequest(room_code=code, character_id=guest_char_id)
        )
        print(f"== 玩家加入 is_new={is_new} member_user={member.user_id} ==")
        assert is_new and rid == room_id

        detail = room_service.get_room_detail(db, room_id, host_id)
        assert len(detail.members) == 2

        # 幂等：重复加入不新增
        _, _, is_new2 = room_member_service.join_room(
            db, guest_id, RoomJoinRequest(room_code=code, character_id=guest_char_id)
        )
        assert is_new2 is False
        print("== 重复加入幂等校验通过 ==")

    # 4) host 开局（AI 走 fallback）
    with SessionLocal() as db:
        result = await room_service.start_game(db, room_id, host_id, host_char_id)
        session_id = result["session_id"]
        opening = result["opening"]
        print(f"\n== 开局完成 session_id={session_id} 场景='{opening.scene_title}' ==")
        print(f"   主任务: {opening.main_task}")
        assert result["detail"].room.status == "playing"

    # 5) 两名玩家各提交一次行动
    for uid, text in (
        (host_id, "我贴着墙根潜行，观察仓库门口的守卫。"),
        (guest_id, "我大步上前，用肩膀撞开仓库的木门。"),
    ):
        with SessionLocal() as db:
            res = await room_action_service.handle_action(db, room_id, uid, text)
            data = res["action_data"]
            events = [e["type"] for e in res["events"]]
            print(f"\n== 行动 user={uid} 事件={events} ==")
            print(f"   玩家消息发言者: {data.player_message.sender_name}")
            if data.check:
                print(f"   检定: {data.check.check_type} d20={data.check.dice_roll} "
                      f"=> {'成功' if data.check.is_success else '失败'}")
            print(f"   AI旁白: {data.story.narration[:60]}...")
            assert "dm.narration" in events

    # 6) 幂等行动：同 client_msg_id 不重复处理
    with SessionLocal() as db:
        r1 = await room_action_service.handle_action(
            db, room_id, host_id, "我再次检查门锁。", client_msg_id="dup-001"
        )
        r2 = await room_action_service.handle_action(
            db, room_id, host_id, "我再次检查门锁。", client_msg_id="dup-001"
        )
        assert r1["duplicate"] is False and r2["duplicate"] is True
        print("\n== 行动幂等（client_msg_id）校验通过 ==")

    # 7) 聊天 + 历史分页
    with SessionLocal() as db:
        chat_service.post_chat(
            db, room_id=room_id, user_id=guest_id, sender_name="鲍勃",
            content="干得漂亮！接下来我掩护你。",
        )
        history = chat_service.list_history(db, room_id, limit=100)
        print(f"\n== 房间事件流共 {len(history)} 条（按 seq 升序）==")
        for m in history:
            print(f"   #{m.seq:>2} [{m.sender_role:>6}/{m.message_type:<9}] "
                  f"{(m.sender_name or ''):<8} {m.content[:40]}")
        seqs = [m.seq for m in history]
        assert seqs == sorted(seqs), "seq 必须单调递增"

        # 分页：取前半段
        page = chat_service.list_history(db, room_id, before_seq=seqs[-1], limit=3)
        assert all(m.seq < seqs[-1] for m in page)
        # 断线重连：after_seq 补齐
        after = chat_service.list_history(db, room_id, after_seq=seqs[2], limit=50)
        assert all(m.seq > seqs[2] for m in after)
        assert len(after) == len(history) - 3
        total = db.query(RoomMessage).filter(RoomMessage.room_id == room_id).count()
        assert total == len(history)

    # 8) dm.ask / GuidanceAgent（默认仅提问者可见）
    with SessionLocal() as db:
        ask_result = await guidance_service.handle_dm_ask(
            db, room_id, guest_id,
            "潜行时检定失败会怎样？",
            sender_name="鲍勃",
            client_msg_id="ask-001",
            visibility="self",
        )
        assert ask_result["duplicate"] is False
        reply = ask_result["reply_message"]
        assert reply is not None and reply.message_type == "guidance"
        print(f"\n== dm.ask 回答: {reply.content[:80]}... ==")

        guest_view = chat_service.list_history(db, room_id, viewer_user_id=guest_id, limit=200)
        host_view = chat_service.list_history(db, room_id, viewer_user_id=host_id, limit=200)
        guest_types = [m.message_type for m in guest_view if m.message_type in ("dm_ask", "guidance")]
        host_types = [m.message_type for m in host_view if m.message_type in ("dm_ask", "guidance")]
        assert "guidance" in guest_types and "dm_ask" in guest_types
        assert "guidance" not in host_types and "dm_ask" not in host_types
        print("== dm.ask 隐私过滤（host 看不到 guest 私密问答）校验通过 ==")

        dup = await guidance_service.handle_dm_ask(
            db, room_id, guest_id,
            "潜行时检定失败会怎样？",
            client_msg_id="ask-001",
        )
        assert dup["duplicate"] is True
        print("== dm.ask 幂等（client_msg_id）校验通过 ==")

    print("\n[OK] 多人房间 P0 + dm.ask 全链路冒烟测试通过 ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

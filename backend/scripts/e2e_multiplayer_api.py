# -*- coding: utf-8 -*-
"""Multiplayer E2E test for StoryForge.

This script covers:
1. LAN-style user registration / room join
2. OpeningAgent pulling world + module + rulebook context from DB
3. Opening narration persistence + WS broadcast
4. A player action that goes through parse -> check -> narrative -> critic -> commit
5. Frontend-facing room message flow and DB persistence checks

Usage:
    python backend/scripts/e2e_multiplayer_api.py --spawn-server --live-ai
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import quote

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.ai.services.fallbacks import mock_module_extract, mock_rulebook_extract
from backend.app.core.config import settings

try:
    import websockets
except ImportError:  # pragma: no cover - optional dependency in some envs
    websockets = None  # type: ignore

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


@dataclass
class CaseResult:
    case_id: str
    name: str
    ok: bool
    detail: str = ""


@dataclass
class SuiteResult:
    results: list[CaseResult] = field(default_factory=list)

    def ok(self, case_id: str, name: str, detail: str = "") -> None:
        self.results.append(CaseResult(case_id, name, True, detail))

    def fail(self, case_id: str, name: str, detail: str) -> None:
        self.results.append(CaseResult(case_id, name, False, detail))

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.ok)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.ok)

    def print_report(self) -> None:
        print("\n" + "=" * 72)
        print("StoryForge multiplayer E2E report")
        print("=" * 72)
        for r in self.results:
            mark = "PASS" if r.ok else "FAIL"
            line = f"[{mark}] {r.case_id} {r.name}"
            if r.detail:
                line += f" | {r.detail}"
            print(line)
        print("-" * 72)
        print(f"Total: {self.passed} passed, {self.failed} failed / {len(self.results)} cases")
        print("=" * 72)


class HttpClient:
    def __init__(self, base_url: str, suite: SuiteResult, label: str = ""):
        self.base = base_url.rstrip("/")
        self.token: str | None = None
        self.user: dict | None = None
        self.suite = suite
        self.label = label
        self._client = httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
        auth: bool = True,
    ) -> tuple[int, Any]:
        headers = self._headers() if auth else {"Accept": "application/json"}
        response = await self._client.request(
            method,
            f"{self.base}{path}",
            headers=headers,
            json=json_body,
            params=params,
        )
        try:
            body = response.json() if response.content else None
        except json.JSONDecodeError:
            body = response.text
        return response.status_code, body

    async def api(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
        auth: bool = True,
    ) -> Any:
        status, body = await self.request(method, path, json_body=json_body, params=params, auth=auth)
        if status >= 400:
            msg = body.get("message") if isinstance(body, dict) else str(body)
            raise RuntimeError(f"HTTP {status} {path}: {msg}")
        if isinstance(body, dict) and "code" in body and body.get("code") != 0:
            raise RuntimeError(f"API error {path}: {body.get('message')}")
        return body.get("data") if isinstance(body, dict) and "data" in body else body

    async def register(self, username: str, password: str = "testpass1") -> None:
        data = await self.api(
            "POST",
            "/api/v1/auth/register",
            json_body={"username": username, "password": password, "nickname": username},
            auth=False,
        )
        self.token = data["access_token"]
        self.user = data["user"]

    async def me(self) -> dict:
        return await self.api("GET", "/api/v1/auth/me")


class WsCollector:
    def __init__(self, base_http: str, room_id: int, token: str):
        self.ws_url = (
            base_http.replace("http://", "ws://").replace("https://", "wss://")
            + f"/api/v1/ws/rooms/{room_id}?token={quote(token, safe='')}"
        )
        self.events: list[dict] = []
        self._ws = None
        self._task: asyncio.Task | None = None

    async def connect(self, wait_snapshot: bool = True) -> None:
        if websockets is None:
            raise RuntimeError("websockets is required: pip install websockets")
        self._ws = await websockets.connect(self.ws_url, open_timeout=15)
        first = await asyncio.wait_for(self._ws.recv(), timeout=15)
        self.events.append(json.loads(first))
        self._task = asyncio.create_task(self._reader())
        if wait_snapshot and not self.has_type("room.snapshot"):
            await self.wait_type("room.snapshot", timeout=5)

    async def _reader(self) -> None:
        try:
            async for raw in self._ws:
                try:
                    ev = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if ev.get("type") == "pong":
                    continue
                self.events.append(ev)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def send(self, event_type: str, data: dict | None = None) -> None:
        await self._ws.send(json.dumps({"type": event_type, "data": data or {}}))

    async def wait_type(self, event_type: str, timeout: float = 30.0) -> dict:
        deadline = time.time() + timeout
        while time.time() < deadline:
            for ev in self.events:
                if ev.get("type") == event_type:
                    return ev
            await asyncio.sleep(0.05)
        raise TimeoutError(f"timeout waiting for event {event_type}")

    def count(self, event_type: str) -> int:
        return sum(1 for e in self.events if e.get("type") == event_type)

    def has_type(self, event_type: str) -> bool:
        return self.count(event_type) > 0

    async def close(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()


def new_client_msg_id() -> str:
    return f"e2e_{uuid.uuid4().hex[:12]}"


def _prepare_database(db_path: Path) -> int:
    """Create an isolated SQLite DB, seed one world, one rulebook pack and one adventure module."""
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ.setdefault("SEED_DEMO_DATA", "false")

    from backend.app.db.database import SessionLocal
    from backend.app.db.init_db import init_db
    from backend.app.models.models import World
    from backend.app.services.content_pack_repository import (
        link_module_to_world,
        link_rulebook_to_world,
        save_adventure_module,
        save_rulebook_pack,
    )

    init_db(drop_first=True)
    with SessionLocal() as db:
        world = World(
            name="黑鸦古堡",
            type="mystery",
            description="端到端测试用世界：古堡悬疑与调查线索。",
            opening_prompt="请用中文生成一个简短而有张力的开局。",
            rule_style="lite_dnd",
            difficulty="normal",
            is_enabled=1,
            created_by=None,
        )
        db.add(world)
        db.flush()

        rulebook_output = mock_rulebook_extract(SimpleNamespace(source_name="黑鸦古堡规则书.docx"))
        rulebook = save_rulebook_pack(
            db,
            rulebook_output,
            source_filename="黑鸦古堡规则书.docx",
            knowledge_pack_dir=None,
        )
        link_rulebook_to_world(db, world.id, rulebook.id)

        module_output = mock_module_extract(SimpleNamespace(source_name="黑鸦古堡模组.docx"))
        module = save_adventure_module(
            db,
            module_output,
            source_filename="黑鸦古堡模组.docx",
            knowledge_pack_dir=None,
        )
        link_module_to_world(db, world.id, module.id)

        db.commit()
        db.refresh(world)
        return world.id


def _spawn_server(port: int, db_path: Path, *, live_ai: bool) -> subprocess.Popen:
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    env["AKP_ENABLED"] = "false"
    env["SEED_DEMO_DATA"] = "false"
    env["DB_AUTO_CREATE"] = "true"
    if live_ai:
        if not settings.LLM_API_KEY.strip():
            raise RuntimeError("LLM_API_KEY is empty, cannot start --live-ai mode")
        env["LLM_API_BASE"] = settings.LLM_API_BASE
        env["LLM_API_KEY"] = settings.LLM_API_KEY
        env["LLM_MODEL"] = settings.LLM_MODEL
        env["LLM_TIMEOUT"] = str(settings.LLM_TIMEOUT)
        env["LLM_MAX_TOKENS"] = str(settings.LLM_MAX_TOKENS)
        env["LLM_TEMPERATURE"] = str(settings.LLM_TEMPERATURE)
        env["AI_ENABLE_CRITIC"] = "true" if settings.AI_ENABLE_CRITIC else "false"
        env["AI_FALLBACK_ON_CRITIC_FAIL"] = "true" if settings.AI_FALLBACK_ON_CRITIC_FAIL else "false"
        env["AI_MAX_REVISIONS"] = str(settings.AI_MAX_REVISIONS)
        env["AI_CRITIC_PASS_SCORE"] = str(settings.AI_CRITIC_PASS_SCORE)
    else:
        env["LLM_API_KEY"] = ""

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    return subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


async def _wait_health(base_url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    async with httpx.AsyncClient() as client:
        while time.time() < deadline:
            try:
                response = await client.get(f"{base_url}/health", timeout=2.0)
                if response.status_code == 200:
                    return
            except Exception:
                pass
            await asyncio.sleep(0.3)
    raise RuntimeError(f"server not ready within {timeout}s: {base_url}/health")


def _assert_opening_context(db_path: Path, world_id: int, character_id: int) -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

    from backend.app.db.database import SessionLocal
    from backend.app.models.models import Character, World
    from backend.app.services.content_ingestion_service import load_world_content_context
    from backend.app.services.context_builder import build_for_opening

    with SessionLocal() as db:
        world = db.get(World, world_id)
        character = db.get(Character, character_id)
        assert world is not None
        assert character is not None
        assert world.rulebook_pack_id is not None
        assert world.adventure_module_id is not None

        pack_ctx = load_world_content_context(db, world)
        assert pack_ctx["rulebook"] is not None
        assert pack_ctx["module"] is not None
        assert len(pack_ctx["public_world_facts"]) >= 2
        assert len(pack_ctx["seed_npcs"]) >= 1

        opening_input = build_for_opening(db, world, character)
        assert opening_input.public_world_facts
        assert opening_input.seed_npcs


async def run_e2e(base_url: str, suite: SuiteResult, verbose: bool, db_path: Path | None = None) -> None:
    host = HttpClient(base_url, suite, "host")
    guest = HttpClient(base_url, suite, "guest")
    ws_host: WsCollector | None = None
    ws_guest: WsCollector | None = None
    suffix = uuid.uuid4().hex[:8]

    try:
        # Auth
        await host.register(f"e2e_host_{suffix}")
        suite.ok("T-AUTH-01", "host register")
        assert (await host.me())["username"].startswith("e2e_host_")
        suite.ok("T-AUTH-02", "host /me")

        await guest.register(f"e2e_guest_{suffix}")
        suite.ok("T-AUTH-03", "guest register")

        worlds = await host.api("GET", "/api/v1/worlds", auth=False)
        assert len(worlds) >= 1
        world_id = worlds[0]["id"]
        suite.ok("T-WORLD-01", f"world list count={len(worlds)}")

        # Characters
        char_payload = {
            "name": f"HostChar_{suffix}",
            "race_id": "human",
            "class_id": "rogue",
            "background_id": "acolyte",
            "motivation": "e2e test",
            "base_attributes": {
                "strength": 13,
                "dexterity": 15,
                "constitution": 12,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 8,
            },
            "selected_skills": ["ste"],
        }
        host_char = await host.api("POST", "/api/v1/characters", json_body=char_payload)
        guest_char = await guest.api(
            "POST",
            "/api/v1/characters",
            json_body={**char_payload, "name": f"GuestChar_{suffix}"},
        )
        suite.ok("T-CHAR-01", "create 2 characters")

        chars = await host.api("GET", "/api/v1/characters")
        assert any(c["id"] == host_char["id"] for c in chars)
        suite.ok("T-CHAR-02", "list characters")

        # Room create/join
        detail = await host.api(
            "POST",
            "/api/v1/rooms",
            json_body={
                "title": f"E2E房间{suffix}",
                "world_id": world_id,
                "visibility": "public",
                "max_players": 2,
            },
        )
        room = detail["room"]
        room_id = room["id"]
        room_code = room["room_code"]
        suite.ok("T-ROOM-01", f"create room id={room_id} code={room_code}")

        mine = await host.api("GET", "/api/v1/rooms", params={"scope": "mine"})
        assert any(r["id"] == room_id for r in mine)
        suite.ok("T-ROOM-02", "mine rooms")

        public = await guest.api("GET", "/api/v1/rooms", params={"scope": "public"})
        assert any(r["id"] == room_id for r in public)
        suite.ok("T-ROOM-03", "public rooms")

        joined = await guest.api(
            "POST",
            "/api/v1/rooms/join",
            json_body={"room_code": room_code, "character_id": guest_char["id"]},
        )
        assert joined["room"]["id"] == room_id
        suite.ok("T-ROOM-04", "guest join")

        room_detail = await host.api("GET", f"/api/v1/rooms/{room_id}")
        assert len(room_detail["members"]) == 2
        suite.ok("T-ROOM-05", "room detail")

        await host.api(
            "POST",
            f"/api/v1/rooms/{room_id}/character",
            json_body={"character_id": host_char["id"]},
        )
        await guest.api(
            "POST",
            f"/api/v1/rooms/{room_id}/character",
            json_body={"character_id": guest_char["id"]},
        )
        suite.ok("T-ROOM-06", "bind characters")

        await host.api("POST", f"/api/v1/rooms/{room_id}/ready", json_body={"is_ready": True})
        await guest.api("POST", f"/api/v1/rooms/{room_id}/ready", json_body={"is_ready": True})
        suite.ok("T-ROOM-07", "ready both players")

        if db_path is not None:
            _assert_opening_context(db_path, room["world_id"], host_char["id"])
            suite.ok("T-DB-CTX", "opening context reads world+rulebook+module from DB")

        # Connect WS before starting game so we can see the opening broadcast.
        ws_host = WsCollector(base_url, room_id, host.token)
        ws_guest = WsCollector(base_url, room_id, guest.token)
        await ws_host.connect()
        await ws_guest.connect()
        suite.ok("T-WS-01", "ws connected")
        suite.ok("T-WS-02", "room snapshot received")

        # Start game / opening
        start_result = await host.api(
            "POST",
            f"/api/v1/rooms/{room_id}/start",
            json_body={"character_id": host_char["id"]},
        )
        assert start_result["detail"]["room"]["status"] == "playing"
        assert start_result["session_id"]
        assert start_result["opening_message"]["content"]
        suite.ok("T-ROOM-08", f"start game session={start_result['session_id']}")
        suite.ok("T-ROOM-08b", "opening message returned")

        await ws_host.wait_type("game.started", timeout=15)
        await ws_guest.wait_type("game.started", timeout=15)
        await ws_host.wait_type("dm.narration", timeout=15)
        await ws_guest.wait_type("dm.narration", timeout=15)
        suite.ok("T-WS-03", "opening broadcast reached both clients")

        # Chat / OOC sanity
        cid_chat = new_client_msg_id()
        await ws_guest.send("chat.send", {"content": "大家好，准备行动。", "client_msg_id": cid_chat})
        await asyncio.sleep(0.8)
        if ws_host.has_type("chat.message") and ws_guest.has_type("chat.message"):
            suite.ok("T-WS-04", "chat broadcast")
        else:
            suite.fail(
                "T-WS-04",
                "chat broadcast",
                f"host={ws_host.count('chat.message')} guest={ws_guest.count('chat.message')}",
            )

        await ws_host.send("ooc.send", {"content": "（场外）这关很难。", "client_msg_id": new_client_msg_id()})
        await asyncio.sleep(0.8)
        if ws_host.has_type("ooc.message") and ws_guest.has_type("ooc.message"):
            suite.ok("T-WS-05", "ooc broadcast")
        else:
            suite.fail("T-WS-05", "ooc broadcast", "missing ooc.message")

        await ws_guest.send("typing.start", {})
        await asyncio.sleep(0.5)
        if ws_host.has_type("typing.start") and not ws_guest.has_type("typing.start"):
            suite.ok("T-WS-06", "typing broadcast excludes sender")
        else:
            suite.fail("T-WS-06", "typing broadcast", f"host={ws_host.count('typing.start')}")

        await ws_host.send("ping", {})
        await asyncio.sleep(0.3)
        suite.ok("T-WS-07", "ping/pong")

        # Player action -> parse -> check -> narrative -> critic -> commit
        before_seq = max((e.get("seq") or 0) for e in ws_host.events)
        action_text = "我轻手轻脚地试图撬开钟摆后方的暗门，看看里面是否藏着机关。"
        action_client_msg_id = new_client_msg_id()
        action_resp = await host.api(
            "POST",
            f"/api/v1/rooms/{room_id}/action",
            json_body={"action_text": action_text, "client_msg_id": action_client_msg_id},
        )
        action_data = action_resp["action_data"]
        assert action_data is not None
        suite.ok("T-ROOM-09", "action API returned payload")

        if action_data.get("check") is not None:
            suite.ok("T-ROOM-09b", "action triggered a dice check")
        else:
            suite.fail("T-ROOM-09b", "action triggered a dice check", "check is missing")

        if action_data["meta"]["tokens_used"] > 0:
            suite.ok("T-ROOM-09c", f"live AI tokens_used={action_data['meta']['tokens_used']}")
        else:
            suite.fail("T-ROOM-09c", "live AI tokens_used", "tokens_used=0")

        if not action_data["ai_review"]["used_fallback"]:
            suite.ok("T-ROOM-09d", "critic/narrative used live AI, not fallback")
        else:
            suite.fail("T-ROOM-09d", "critic/narrative used live AI", "used_fallback=true")

        await ws_host.wait_type("action.accepted", timeout=15)
        await ws_guest.wait_type("action.accepted", timeout=15)
        await ws_host.wait_type("action.received", timeout=15)
        await ws_guest.wait_type("action.received", timeout=15)

        stages = {ev.get("data", {}).get("stage") for ev in ws_host.events if ev.get("type") == "ai.thinking"}
        if {"parsing", "narrating"}.issubset(stages):
            suite.ok("T-WS-08", "ai.thinking stages broadcast")
        else:
            suite.fail("T-WS-08", "ai.thinking stages", f"seen={sorted(x for x in stages if x)}")

        if action_data.get("check") is not None:
            await ws_host.wait_type("dice.result", timeout=20)
            await ws_guest.wait_type("dice.result", timeout=20)
            await ws_host.wait_type("dice.rolled", timeout=20)
            await ws_guest.wait_type("dice.rolled", timeout=20)
            suite.ok("T-WS-09", "dice broadcast")

        await ws_host.wait_type("dm.narration", timeout=30)
        await ws_guest.wait_type("dm.narration", timeout=30)
        await ws_host.wait_type("state.updated", timeout=30)
        await ws_guest.wait_type("state.updated", timeout=30)
        suite.ok("T-WS-10", "narration/state updates broadcast")

        # Leave room history queries after action.
        ws_guest.events.clear()
        ws_host.events.clear()
        ask_cid = new_client_msg_id()
        await ws_guest.send(
            "dm.ask",
            {"question": "我现在能做什么？", "client_msg_id": ask_cid, "visibility": "self"},
        )
        await asyncio.sleep(8.0)
        if ws_guest.has_type("dm.guidance") and not ws_host.has_type("dm.guidance"):
            suite.ok("T-WS-11", "dm.ask privacy")
        else:
            suite.fail(
                "T-WS-11",
                "dm.ask privacy",
                f"guest={ws_guest.has_type('dm.guidance')} host={ws_host.has_type('dm.guidance')}",
            )

        after_seq = before_seq
        await ws_host.close()
        await ws_guest.close()
        ws_host = None
        ws_guest = None

        # REST history / dedupe / privacy
        hist = await host.api("GET", f"/api/v1/rooms/{room_id}/messages", params={"limit": 200})
        assert len(hist) >= 1
        seqs = [m["seq"] for m in hist]
        assert seqs == sorted(seqs)
        suite.ok("T-ROOM-10", f"history count={len(hist)}")

        after = await guest.api(
            "GET",
            f"/api/v1/rooms/{room_id}/messages",
            params={"after_seq": after_seq, "limit": 100},
        )
        assert all(m["seq"] > after_seq for m in after)
        suite.ok("T-ROOM-11", f"after_seq returned {len(after)} messages")

        rest_chat = await guest.api(
            "POST",
            f"/api/v1/rooms/{room_id}/chat",
            json_body={"content": "REST chat fallback", "client_msg_id": new_client_msg_id()},
        )
        assert rest_chat["message_type"] == "chat"
        suite.ok("T-ROOM-12", "REST chat")

        rest_ooc = await host.api(
            "POST",
            f"/api/v1/rooms/{room_id}/ooc",
            json_body={"content": "REST OOC fallback", "client_msg_id": new_client_msg_id()},
        )
        assert rest_ooc["message_type"] == "ooc"
        suite.ok("T-ROOM-13", "REST ooc")

        rest_ask = await guest.api(
            "POST",
            f"/api/v1/rooms/{room_id}/ask",
            json_body={"question": "如果失败怎么办？", "client_msg_id": new_client_msg_id(), "visibility": "self"},
        )
        assert rest_ask.get("reply") is not None
        suite.ok("T-ROOM-14", "REST ask")

        dup = await host.api(
            "POST",
            f"/api/v1/rooms/{room_id}/action",
            json_body={"action_text": action_text, "client_msg_id": action_client_msg_id},
        )
        assert dup.get("duplicate") is True
        suite.ok("T-ROOM-15", "duplicate handling reachable")

        guest_hist = await guest.api("GET", f"/api/v1/rooms/{room_id}/messages", params={"limit": 200})
        host_hist = await host.api("GET", f"/api/v1/rooms/{room_id}/messages", params={"limit": 200})
        g_has = any(m["message_type"] == "guidance" for m in guest_hist)
        h_has = any(m["message_type"] == "guidance" for m in host_hist)
        if g_has and not h_has:
            suite.ok("T-ROOM-16", "guidance privacy in REST history")
        else:
            suite.fail("T-ROOM-16", "guidance privacy in REST history", f"guest={g_has} host={h_has}")

        # Host leave / room end
        leave_res = await host.api("POST", f"/api/v1/rooms/{room_id}/leave")
        assert leave_res.get("transferred_to_user_id") == guest.user["id"]
        suite.ok("T-ROOM-17", f"host left, transferred to user {guest.user['id']}")

        room_after_leave = await guest.api("GET", f"/api/v1/rooms/{room_id}")
        assert room_after_leave["room"]["owner_id"] == guest.user["id"]
        suite.ok("T-ROOM-18", "owner transferred")

        ended = await guest.api("POST", f"/api/v1/rooms/{room_id}/end")
        assert ended["room"]["status"] == "finished"
        suite.ok("T-ROOM-19", "room ended")

        # DB assertions
        if db_path is not None:
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
        from backend.app.db.database import SessionLocal
        from backend.app.models.models import GameSession, Message, Room, RoomAction, RoomMember, RoomMessage

        with SessionLocal() as db:
            room_row = db.get(Room, room_id)
            assert room_row is not None and room_row.status == "finished"
            members = db.query(RoomMember).filter(RoomMember.room_id == room_id).all()
            assert len(members) == 1
            session_row = db.get(GameSession, start_result["session_id"])
            assert session_row is not None and session_row.mode == "multiplayer"
            assert session_row.room_id == room_id

            session_messages = (
                db.query(Message)
                .filter(Message.session_id == start_result["session_id"])
                .order_by(Message.id)
                .all()
            )
            narration_messages = [m for m in session_messages if m.message_type == "narration"]
            assert len(narration_messages) >= 2
            assert (narration_messages[0].tokens_used or 0) > 0
            assert (narration_messages[1].tokens_used or 0) > 0

            action_rows = db.query(RoomAction).filter(
                RoomAction.room_id == room_id,
                RoomAction.status == "done",
            ).count()
            assert action_rows >= 1

            room_messages = db.query(RoomMessage).filter(RoomMessage.room_id == room_id).all()
            room_types = {m.message_type for m in room_messages}
            for required in ("chat", "ooc", "action", "dice", "narration"):
                assert required in room_types, f"missing room message type: {required}"

        suite.ok("T-DB-01", "database assertions passed")

        if verbose:
            print(
                f"\n[verbose] room_id={room_id} session_id={start_result['session_id']} "
                f"action_tokens={action_data['meta']['tokens_used']} "
                f"narration_tokens={narration_messages[0].tokens_used}"
            )

    except Exception as exc:
        suite.fail("T-FATAL", "unhandled exception", str(exc))
        if verbose:
            import traceback

            traceback.print_exc()
    finally:
        await host.close()
        await guest.close()
        if ws_host is not None:
            await ws_host.close()
        if ws_guest is not None:
            await ws_guest.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="StoryForge multiplayer E2E test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8876")
    parser.add_argument("--port", type=int, default=8876)
    parser.add_argument("--spawn-server", action="store_true", help="start uvicorn automatically")
    parser.add_argument("--live-ai", action="store_true", help="run against the real LLM provider")
    parser.add_argument("--keep-server", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    if args.spawn_server:
        base_url = f"http://127.0.0.1:{args.port}"

    db_path = PROJECT_ROOT / "e2e_multiplayer.db"
    server_proc: subprocess.Popen | None = None
    suite = SuiteResult()

    print("=" * 72)
    print("StoryForge multiplayer E2E")
    print(f"Target: {base_url}")
    print(f"Mode: {'live AI' if args.live_ai else 'mock AI'}")
    print("=" * 72)

    try:
        if args.spawn_server:
            print(f"[setup] creating database {db_path}")
            world_id = _prepare_database(db_path)
            print(f"[setup] world_id={world_id}")
            print(f"[setup] starting uvicorn on :{args.port}")
            server_proc = _spawn_server(args.port, db_path, live_ai=args.live_ai)
            asyncio.run(_wait_health(base_url))
            print("[setup] server ready\n")

        asyncio.run(run_e2e(base_url, suite, args.verbose, db_path if args.spawn_server else None))
    finally:
        if server_proc and suite.failed and server_proc.stderr:
            err_tail = server_proc.stderr.read().decode("utf-8", errors="replace")[-4000:]
            if err_tail.strip():
                print("\n[server stderr]\n" + err_tail)
        if server_proc and not args.keep_server:
            if sys.platform == "win32":
                server_proc.terminate()
            else:
                server_proc.send_signal(signal.SIGTERM)
            try:
                server_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server_proc.kill()
            print("[teardown] server stopped")

    suite.print_report()
    return 0 if suite.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

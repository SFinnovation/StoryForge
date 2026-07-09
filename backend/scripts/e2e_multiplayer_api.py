# -*- coding: utf-8 -*-
"""多人房间 E2E：HTTP + WebSocket 外部接入测试（模拟前端 client.js / wsClient.js）

用法（PowerShell，项目根目录）：
    python backend/scripts/e2e_multiplayer_api.py --spawn-server

可选参数：
    --base-url http://127.0.0.1:8765   # 已有服务时
    --spawn-server                      # 自动起 uvicorn + 独立 sqlite
    --port 8765
    --keep-server                       # 测试后不杀进程
    --verbose

测试方案详见：docs/testing-multiplayer-e2e.md
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
from typing import Any
from urllib.parse import quote

import httpx

try:
    import websockets
except ImportError:
    websockets = None  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ---------------------------------------------------------------------------
# 结果收集
# ---------------------------------------------------------------------------


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
        print("\n" + "=" * 60)
        print("E2E 测试报告")
        print("=" * 60)
        for r in self.results:
            mark = "PASS" if r.ok else "FAIL"
            line = f"[{mark}] {r.case_id} {r.name}"
            if r.detail:
                line += f" — {r.detail}"
            print(line)
        print("-" * 60)
        print(f"合计: {self.passed} 通过, {self.failed} 失败 / {len(self.results)} 项")
        print("=" * 60)


# ---------------------------------------------------------------------------
# HTTP 客户端（模拟 frontend/src/api/client.js）
# ---------------------------------------------------------------------------


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
        h = {"Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

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
        r = await self._client.request(
            method,
            f"{self.base}{path}",
            headers=headers,
            json=json_body,
            params=params,
        )
        try:
            body = r.json() if r.content else None
        except json.JSONDecodeError:
            body = r.text
        return r.status_code, body

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


# ---------------------------------------------------------------------------
# WebSocket 客户端（模拟 frontend/src/api/wsClient.js）
# ---------------------------------------------------------------------------


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
            raise RuntimeError("需要安装 websockets：pip install websockets")
        self._ws = await websockets.connect(self.ws_url, open_timeout=15)
        # 首包同步读取，避免 snapshot 在后台 task 启动前丢失
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
        raise TimeoutError(f"等待事件 {event_type} 超时")

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


# ---------------------------------------------------------------------------
# 服务启动 / 数据库种子
# ---------------------------------------------------------------------------


def _prepare_database(db_path: Path) -> int:
    """初始化测试库并写入一个可用世界，返回 world_id。"""
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ.setdefault("SEED_DEMO_DATA", "false")

    from backend.app.db.database import SessionLocal
    from backend.app.db.init_db import init_db
    from backend.app.models.models import World

    init_db(drop_first=True)
    with SessionLocal() as db:
        world = World(
            name="E2E 测试世界",
            type="fantasy",
            description="端到端测试用世界",
            opening_prompt="Open a short test scene.",
            rule_style="lite_dnd",
            difficulty="normal",
            is_enabled=1,
            created_by=None,
        )
        db.add(world)
        db.commit()
        db.refresh(world)
        return world.id


def _spawn_server(port: int, db_path: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    env["LLM_API_KEY"] = ""
    env["AKP_ENABLED"] = "false"
    env["SEED_DEMO_DATA"] = "false"
    env["DB_AUTO_CREATE"] = "true"
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
                r = await client.get(f"{base_url}/health", timeout=2.0)
                if r.status_code == 200:
                    return
            except Exception:
                pass
            await asyncio.sleep(0.3)
    raise RuntimeError(f"服务未在 {timeout}s 内就绪: {base_url}/health")


# ---------------------------------------------------------------------------
# 主测试流程
# ---------------------------------------------------------------------------


async def run_e2e(base_url: str, suite: SuiteResult, verbose: bool, db_path: Path | None = None) -> None:
    host = HttpClient(base_url, suite, "host")
    guest = HttpClient(base_url, suite, "guest")
    suffix = uuid.uuid4().hex[:8]

    try:
        # --- Phase A: 鉴权与角色 ---
        await host.register(f"e2e_host_{suffix}")
        suite.ok("T-AUTH-01", "Host 注册")
        h_me = await host.me()
        assert h_me["username"].startswith("e2e_host_")
        suite.ok("T-AUTH-02", "Host /auth/me")

        await guest.register(f"e2e_guest_{suffix}")
        suite.ok("T-AUTH-01", "Guest 注册")

        worlds = await host.api("GET", "/api/v1/worlds", auth=False)
        assert len(worlds) >= 1
        world_id = worlds[0]["id"]
        suite.ok("T-WORLD-01", f"GET /worlds ({len(worlds)} 个)")

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
        suite.ok("T-CHAR-01", "创建角色 x2")

        chars = await host.api("GET", "/api/v1/characters")
        assert any(c["id"] == host_char["id"] for c in chars)
        suite.ok("T-CHAR-02", "GET /characters")

        # --- Phase B: 房间 REST 生命周期 ---
        detail = await host.api(
            "POST",
            "/api/v1/rooms",
            json_body={
                "title": f"E2E团_{suffix}",
                "world_id": world_id,
                "visibility": "public",
                "max_players": 2,
            },
        )
        room = detail["room"]
        room_id = room["id"]
        room_code = room["room_code"]
        suite.ok("T-ROOM-01", f"POST /rooms id={room_id} code={room_code}")

        mine = await host.api("GET", "/api/v1/rooms", params={"scope": "mine"})
        assert any(r["id"] == room_id for r in mine)
        suite.ok("T-ROOM-02", "GET /rooms?scope=mine")

        public = await guest.api("GET", "/api/v1/rooms", params={"scope": "public"})
        assert any(r["id"] == room_id for r in public)
        suite.ok("T-ROOM-03", "GET /rooms?scope=public")

        joined = await guest.api(
            "POST",
            "/api/v1/rooms/join",
            json_body={"room_code": room_code, "character_id": guest_char["id"]},
        )
        assert joined["room"]["id"] == room_id
        suite.ok("T-ROOM-04", "POST /rooms/join")

        rd = await host.api("GET", f"/api/v1/rooms/{room_id}")
        assert len(rd["members"]) == 2
        suite.ok("T-ROOM-05", "GET /rooms/{id}")

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
        suite.ok("T-ROOM-06", "POST /rooms/{id}/character")

        await host.api("POST", f"/api/v1/rooms/{room_id}/ready", json_body={"is_ready": True})
        await guest.api("POST", f"/api/v1/rooms/{room_id}/ready", json_body={"is_ready": True})
        suite.ok("T-ROOM-07", "POST /rooms/{id}/ready")

        started = await host.api(
            "POST",
            f"/api/v1/rooms/{room_id}/start",
            json_body={"character_id": host_char["id"]},
        )
        assert started["detail"]["room"]["status"] == "playing"
        session_id = started["session_id"]
        suite.ok("T-ROOM-08", f"POST /rooms/{{id}}/start session={session_id}")

        # --- Phase C: WebSocket 双客户端 ---
        ws_host = WsCollector(base_url, room_id, host.token)
        ws_guest = WsCollector(base_url, room_id, guest.token)
        await ws_host.connect()
        await ws_guest.connect()
        suite.ok("T-WS-01", "双客户端 WS 连接 + 鉴权")
        suite.ok("T-WS-02", "room.snapshot x2")

        # chat via WS
        cid_chat = new_client_msg_id()
        await ws_guest.send("chat.send", {"content": "大家好，准备行动！", "client_msg_id": cid_chat})
        await asyncio.sleep(1.0)
        if ws_host.has_type("chat.message") and ws_guest.has_type("chat.message"):
            suite.ok("T-WS-03", "chat.send")
            suite.ok("T-WS-04", "chat.message 广播")
        else:
            suite.fail("T-WS-04", "chat.message 广播", f"host={ws_host.count('chat.message')} guest={ws_guest.count('chat.message')}")

        # ooc via WS
        await ws_host.send("ooc.send", {"content": "（场外）这关很难", "client_msg_id": new_client_msg_id()})
        await asyncio.sleep(0.8)
        if ws_host.has_type("ooc.message") and ws_guest.has_type("ooc.message"):
            suite.ok("T-WS-05", "ooc.send")
            suite.ok("T-WS-06", "ooc.message 广播")
        else:
            suite.fail("T-WS-06", "ooc.message 广播", "未收到")

        # typing
        await ws_guest.send("typing.start", {})
        await asyncio.sleep(0.5)
        if ws_host.has_type("typing.start") and not ws_guest.has_type("typing.start"):
            suite.ok("T-WS-07", "typing.start（排除发送者）")
        else:
            suite.fail("T-WS-07", "typing.start", f"host={ws_host.count('typing.start')}")

        # ping
        await ws_host.send("ping", {})
        await asyncio.sleep(0.3)
        suite.ok("T-WS-12", "ping/pong")

        # action via WS
        before_seq = max((e.get("seq") or 0) for e in ws_host.events)
        act_cid = new_client_msg_id()
        await ws_host.send("action.submit", {"action_text": "我观察四周寻找线索。", "client_msg_id": act_cid})
        deadline = time.time() + 90
        while time.time() < deadline:
            if ws_host.has_type("dm.narration") or ws_host.has_type("ai.narration"):
                break
            await asyncio.sleep(0.2)
        if ws_host.has_type("action.accepted") or ws_host.has_type("action.received"):
            suite.ok("T-WS-08", "action.submit")
        else:
            suite.fail("T-WS-08", "action.submit", "无 action 回执")
        if ws_host.has_type("dm.narration") or ws_host.has_type("ai.narration"):
            suite.ok("T-WS-09", "行动叙事链路 dm.narration/ai.narration")
        else:
            suite.fail("T-WS-09", "行动叙事链路", f"events={[e.get('type') for e in ws_host.events[-8:]]}")

        # dm.ask privacy
        ws_guest.events.clear()
        ws_host.events.clear()
        ask_cid = new_client_msg_id()
        await ws_guest.send("dm.ask", {"question": "我现在能做什么？", "client_msg_id": ask_cid, "visibility": "self"})
        await asyncio.sleep(8.0)
        guest_guidance = ws_guest.has_type("dm.guidance")
        host_guidance = ws_host.has_type("dm.guidance")
        if guest_guidance and not host_guidance:
            suite.ok("T-WS-10", "dm.ask")
            suite.ok("T-WS-11", "dm.guidance 仅提问者")
        else:
            suite.fail("T-WS-11", "dm.guidance 隐私", f"guest={guest_guidance} host={host_guidance}")

        await ws_host.close()
        await ws_guest.close()

        # --- Phase D: REST 回退与分页 ---
        hist = await host.api("GET", f"/api/v1/rooms/{room_id}/messages", params={"limit": 200})
        assert len(hist) >= 1
        seqs = [m["seq"] for m in hist]
        assert seqs == sorted(seqs)
        suite.ok("T-ROOM-09", f"GET /messages ({len(hist)} 条, seq 单调)")

        after = await guest.api(
            "GET",
            f"/api/v1/rooms/{room_id}/messages",
            params={"after_seq": before_seq, "limit": 100},
        )
        assert all(m["seq"] > before_seq for m in after)
        suite.ok("T-WS-13", f"after_seq 补消息 ({len(after)} 条)")

        rest_chat = await guest.api(
            "POST",
            f"/api/v1/rooms/{room_id}/chat",
            json_body={"content": "REST 聊天回退", "client_msg_id": new_client_msg_id()},
        )
        assert rest_chat["message_type"] == "chat"
        suite.ok("T-ROOM-10", "POST /chat REST 回退")

        rest_ooc = await host.api(
            "POST",
            f"/api/v1/rooms/{room_id}/ooc",
            json_body={"content": "REST OOC", "client_msg_id": new_client_msg_id()},
        )
        assert rest_ooc["message_type"] == "ooc"
        suite.ok("T-ROOM-11", "POST /ooc REST 回退")

        rest_ask = await guest.api(
            "POST",
            f"/api/v1/rooms/{room_id}/ask",
            json_body={"question": "检定失败会怎样？", "client_msg_id": new_client_msg_id(), "visibility": "self"},
        )
        assert rest_ask.get("reply") is not None
        suite.ok("T-ROOM-12", "POST /ask REST 回退")

        # 幂等 action：复用 WS 阶段已提交的 client_msg_id
        dup2 = await host.api(
            "POST",
            f"/api/v1/rooms/{room_id}/action",
            json_body={"action_text": "我观察四周寻找线索。", "client_msg_id": act_cid},
        )
        assert dup2.get("duplicate") is True
        suite.ok("T-ROOM-13", "POST /action 幂等 client_msg_id")

        # 隐私：host 历史看不到 guest 私密 guidance
        guest_hist = await guest.api("GET", f"/api/v1/rooms/{room_id}/messages", params={"limit": 200})
        host_hist = await host.api("GET", f"/api/v1/rooms/{room_id}/messages", params={"limit": 200})
        g_has = any(m["message_type"] == "guidance" for m in guest_hist)
        h_has = any(m["message_type"] == "guidance" for m in host_hist)
        if g_has and not h_has:
            suite.ok("T-ROOM-09b", "dm.ask 历史隐私过滤")
        else:
            suite.fail("T-ROOM-09b", "dm.ask 历史隐私过滤", f"guest={g_has} host={h_has}")

        # --- Phase E: host 转让 + 结束 ---
        leave_res = await host.api("POST", f"/api/v1/rooms/{room_id}/leave")
        assert leave_res.get("transferred_to_user_id") == guest.user["id"]
        suite.ok("T-ROOM-14", f"host leave 转让 → user {guest.user['id']}")

        rd2 = await guest.api("GET", f"/api/v1/rooms/{room_id}")
        assert rd2["room"]["owner_id"] == guest.user["id"]
        suite.ok("T-ROOM-14b", "转让后 owner_id 更新")

        ended = await guest.api("POST", f"/api/v1/rooms/{room_id}/end")
        assert ended["room"]["status"] == "finished"
        suite.ok("T-ROOM-15", "POST /rooms/{id}/end")

        # --- Phase F: 数据库断言 ---
        if db_path is not None:
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
        from backend.app.db.database import SessionLocal
        from backend.app.models.models import GameSession, Room, RoomAction, RoomMember, RoomMessage

        with SessionLocal() as db:
            r = db.get(Room, room_id)
            assert r is not None and r.status == "finished"
            members = db.query(RoomMember).filter(RoomMember.room_id == room_id).all()
            assert len(members) == 1  # host 已离开
            msgs = db.query(RoomMessage).filter(RoomMessage.room_id == room_id).count()
            assert msgs >= 5
            actions = db.query(RoomAction).filter(RoomAction.room_id == room_id, RoomAction.status == "done").count()
            assert actions >= 1
            sess = db.get(GameSession, session_id)
            assert sess is not None and sess.mode == "multiplayer" and sess.room_id == room_id
            types = {m.message_type for m in db.query(RoomMessage).filter(RoomMessage.room_id == room_id).all()}
            for t in ("chat", "ooc", "narration"):
                assert t in types, f"缺少 message_type={t}"
        suite.ok("T-DB-01", f"数据库断言通过 (messages={msgs}, actions_done>={actions})")

        if verbose:
            print(f"\n[verbose] room_id={room_id} session_id={session_id} message_types={sorted(types)}")

    except Exception as exc:
        suite.fail("T-FATAL", "未捕获异常", str(exc))
        if verbose:
            import traceback
            traceback.print_exc()
    finally:
        await host.close()
        await guest.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="多人房间 E2E API/WS 测试")
    parser.add_argument("--base-url", default="http://127.0.0.1:8876")
    parser.add_argument("--port", type=int, default=8876)
    parser.add_argument("--spawn-server", action="store_true", help="自动启动 uvicorn")
    parser.add_argument("--keep-server", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    if args.spawn_server:
        base_url = f"http://127.0.0.1:{args.port}"

    db_path = PROJECT_ROOT / "e2e_multiplayer.db"
    server_proc: subprocess.Popen | None = None
    suite = SuiteResult()

    print("=" * 60)
    print("StoryForge 多人房间 E2E 测试")
    print(f"目标: {base_url}")
    print("方案: docs/testing-multiplayer-e2e.md")
    print("=" * 60)

    try:
        if args.spawn_server:
            print(f"\n[setup] 初始化数据库 {db_path}")
            world_id = _prepare_database(db_path)
            print(f"[setup] world_id={world_id}")
            print(f"[setup] 启动 uvicorn :{args.port} (LLM mock)")
            server_proc = _spawn_server(args.port, db_path)
            asyncio.run(_wait_health(base_url))
            print("[setup] 服务就绪\n")

        asyncio.run(run_e2e(base_url, suite, args.verbose, db_path if args.spawn_server else None))
    finally:
        if server_proc and suite.failed and server_proc.stderr:
            err_tail = server_proc.stderr.read().decode("utf-8", errors="replace")[-4000:]
            if err_tail.strip():
                print("\n[server stderr 尾部]\n" + err_tail)
        if server_proc and not args.keep_server:
            if sys.platform == "win32":
                server_proc.terminate()
            else:
                server_proc.send_signal(signal.SIGTERM)
            try:
                server_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server_proc.kill()
            print("\n[teardown] 测试服务已停止")

    suite.print_report()
    return 0 if suite.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

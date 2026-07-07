"""FastAPI 行动接口集成测试（httpx ASGI，无需启动服务器）。"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_storyforge_api.db")

from httpx import ASGITransport, AsyncClient

from app.db.init_db import reset_demo_db
from app.main import app


async def main() -> None:
    reset_demo_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start = await client.post(
            "/api/v1/sessions/start",
            json={"world_id": 2, "character_id": 1},
        )
        assert start.status_code == 200, start.text
        session_id = start.json()["data"]["session"]["id"]

        resp = await client.post(
            f"/api/v1/sessions/{session_id}/action",
            json={"action_text": "我想先观察大厅，看看有没有异常线索。"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]

        assert data["check"]["attribute_used"] == "wisdom"
        assert data["story"]["narration"]
        assert data["ai_review"]["approved"] is True
        assert data["ai_review"]["overall_score"] >= 80
        assert "latency_ms" in data["meta"]
        assert "tokens_used" in data["meta"]
        assert isinstance(data["story"]["next_options"], list)

        print("=== API 集成测试通过 ===")
        print(f"session_id: {session_id}")
        print(f"dice_roll: {data['check']['dice_roll']}")
        print(f"meta.latency_ms: {data['meta']['latency_ms']}")


if __name__ == "__main__":
    asyncio.run(main())

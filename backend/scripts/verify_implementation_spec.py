"""对照 implementation-spec 的完整闭环验证脚本。"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# 使用独立测试库，避免污染开发库
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_storyforge_verify.db")

from httpx import ASGITransport, AsyncClient

from backend.app.db.init_db import reset_demo_db
from backend.app.main import app


REQUIRED_ACTION_FIELDS = {
    "player_message",
    "check",
    "story",
    "session_meta",
    "ai_review",
    "meta",
}


async def main() -> None:
    reset_demo_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # health
        r = await client.get("/health")
        assert r.status_code == 200

        # 1. 开局 — POST /sessions/start
        r = await client.post(
            "/api/v1/sessions/start",
            json={"world_id": 2, "character_id": 1},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["code"] == 0
        assert "opening" in body["data"]
        assert body["data"]["opening"]["narration"]
        assert body["data"]["session"]["status"] == "playing"
        session_id = body["data"]["session"]["id"]
        print(f"[OK] sessions/start session_id={session_id}")

        # 2. 行动 — POST /sessions/{id}/action
        r = await client.post(
            f"/api/v1/sessions/{session_id}/action",
            json={"action_text": "我想先观察大厅，看看有没有异常线索。"},
        )
        assert r.status_code == 200, r.text
        action_body = r.json()
        assert action_body["code"] == 0
        data = action_body["data"]
        assert REQUIRED_ACTION_FIELDS <= set(data.keys())
        assert data["story"]["narration"]
        assert data["ai_review"]["approved"] is True
        assert "tokens_used" in data["meta"]
        assert data["check"] is not None
        assert 1 <= data["check"]["dice_roll"] <= 20
        print(f"[OK] action dice_roll={data['check']['dice_roll']} success={data['check']['is_success']}")

        # 3. 消息持久化 — GET /sessions/{id}/messages
        r = await client.get(f"/api/v1/sessions/{session_id}/messages")
        assert r.status_code == 200
        messages = r.json()["data"]
        assert len(messages) >= 3  # opening + player + dice + story (至少3+)
        print(f"[OK] messages persisted count={len(messages)}")

        # 4. meta / facts / ai-reviews (P1 预留接口)
        r = await client.get(f"/api/v1/sessions/{session_id}/meta")
        assert r.status_code == 200
        assert "clue_pressure" in r.json()["data"]

        r = await client.get(f"/api/v1/sessions/{session_id}/facts?scope=player_known")
        assert r.status_code == 200
        assert "facts" in r.json()["data"]

        r = await client.get(f"/api/v1/sessions/{session_id}/ai-reviews")
        assert r.status_code == 200
        assert len(r.json()["data"]["reviews"]) >= 1
        print("[OK] meta / facts / ai-reviews")

        # 5. 结束本局
        r = await client.post(f"/api/v1/sessions/{session_id}/end")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "finished"
        print("[OK] sessions/end")

        # 6. 生成报告 — SummaryAgent
        r = await client.post(f"/api/v1/sessions/{session_id}/report/generate")
        assert r.status_code == 200
        report = r.json()["data"]
        assert report["story_summary"]
        print(f"[OK] report/generate len={len(report['story_summary'])}")

        r = await client.get(f"/api/v1/sessions/{session_id}/report")
        assert r.status_code == 200
        assert r.json()["data"]["story_summary"]
        print("[OK] report/get")

        # 7. finished 后禁止行动
        r = await client.post(
            f"/api/v1/sessions/{session_id}/action",
            json={"action_text": "继续调查"},
        )
        assert r.status_code == 409
        print("[OK] finished session rejects action")

    print("\n=== implementation-spec 闭环验证全部通过 ===")


if __name__ == "__main__":
    asyncio.run(main())

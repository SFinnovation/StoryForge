"""前端联调契约测试。

覆盖前端接入时最常用的 API：
- auth/register, auth/login, auth/me
- rules/dnd5e/summary, rules/dnd5e/skills
- worlds
- characters
- sessions/start, sessions/{id}, sessions/{id}/action
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_storyforge_frontend_contract.db")

from httpx import ASGITransport, AsyncClient

from backend.app.db.init_db import reset_demo_db
from backend.app.main import app


async def main() -> None:
    reset_demo_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={"username": "frontend_user", "password": "secret123", "nickname": "前端联调"},
        )
        assert register.status_code == 201, register.text
        token = register.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        login = await client.post(
            "/api/v1/auth/login",
            json={"username": "frontend_user", "password": "secret123"},
        )
        assert login.status_code == 200, login.text
        assert login.json()["data"]["user"]["username"] == "frontend_user"

        me = await client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200, me.text
        assert me.json()["data"]["nickname"] == "前端联调"

        rules_summary = await client.get("/api/v1/rules/dnd5e/summary")
        assert rules_summary.status_code == 200, rules_summary.text
        rules_data = rules_summary.json()["data"]
        assert rules_data["races"] and rules_data["classes"] and rules_data["backgrounds"]

        skills = await client.get("/api/v1/rules/dnd5e/skills")
        assert skills.status_code == 200, skills.text
        assert len(skills.json()["data"]["skills"]) == 18

        worlds = await client.get("/api/v1/worlds")
        assert worlds.status_code == 200, worlds.text
        assert len(worlds.json()["data"]) >= 1

        character = await client.post(
            "/api/v1/characters",
            headers=headers,
            json={
                "name": "艾琳",
                "race_id": "high-elf",
                "class_id": "rogue",
                "background_id": "acolyte",
                "motivation": "寻找失踪的导师",
                "ability_assignment": "standard_array",
                "base_attributes": {
                    "strength": 8,
                    "dexterity": 15,
                    "constitution": 12,
                    "intelligence": 14,
                    "wisdom": 13,
                    "charisma": 10,
                },
                "selected_skills": ["ste", "inv", "prc", "ins"],
            },
        )
        assert character.status_code == 201, character.text
        character_data = character.json()["data"]
        assert character_data["attributes"]["dexterity"] == 17
        assert character_data["max_hp"] == 9
        assert "ste" in character_data["skills"]
        character_id = character_data["id"]

        start = await client.post(
            "/api/v1/sessions/start",
            headers=headers,
            json={"world_id": 2, "character_id": character_id, "title": "前端联调房间", "difficulty": "easy"},
        )
        assert start.status_code == 200, start.text
        session_data = start.json()["data"]["session"]
        assert session_data["title"] == "前端联调房间"
        assert session_data["difficulty"] == "easy"
        session_id = session_data["id"]

        detail = await client.get(f"/api/v1/sessions/{session_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        assert detail.json()["data"]["messages"]

        action = await client.post(
            f"/api/v1/sessions/{session_id}/action",
            headers=headers,
            json={"action_text": "我悄悄绕到窗边观察房间。"},
        )
        assert action.status_code == 200, action.text
        action_data = action.json()["data"]
        assert action_data["check"]["dc"] == 10
        assert action_data["story"]["narration"]
        assert action_data["session_meta"]["current_scene"]

    print("=== frontend contract test passed ===")


if __name__ == "__main__":
    asyncio.run(main())

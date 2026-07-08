from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient


def _configure_test_env() -> None:
    db_path = Path(tempfile.gettempdir()) / "storyforge_admin_api_test.db"
    if db_path.exists():
        db_path.unlink()
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["DB_AUTO_CREATE"] = "true"
    os.environ["SEED_DEMO_DATA"] = "true"
    os.environ["ADMIN_USERNAME"] = "admin"
    os.environ["ADMIN_PASSWORD"] = "admin123"
    os.environ["LLM_API_KEY"] = ""


def main() -> None:
    _configure_test_env()

    from backend.app.main import app

    with TestClient(app) as client:
        admin_login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert admin_login.status_code == 200, admin_login.text
        token = admin_login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        world = client.post(
            "/api/v1/admin/worlds",
            headers=headers,
            json={
                "name": "测试世界观",
                "type": "custom",
                "description": "管理员接口测试世界观",
                "modules": [{"name": "测试模组", "description": "管理员接口测试模组"}],
            },
        )
        assert world.status_code == 201, world.text
        world_id = world.json()["data"]["id"]
        module_id = world.json()["data"]["modules"][0]["id"]

        worlds = client.get("/api/v1/admin/worlds", headers=headers)
        assert worlds.status_code == 200, worlds.text
        assert any(item["id"] == world_id for item in worlds.json()["data"]["items"])

        delete_module = client.delete(f"/api/v1/admin/modules/{module_id}", headers=headers)
        assert delete_module.status_code == 200, delete_module.text

        register = client.post(
            "/api/v1/auth/register",
            json={
                "username": "admin_api_user",
                "password": "old-pass-123",
                "nickname": "Admin API User",
                "email": "admin-api-user@example.com",
            },
        )
        assert register.status_code == 201, register.text
        user_id = register.json()["data"]["user"]["id"]

        reset = client.post(
            f"/api/v1/admin/users/{user_id}/reset-password",
            headers=headers,
            json={"new_password": "new-pass-123", "reason": "测试重置"},
        )
        assert reset.status_code == 200, reset.text

        ban = client.post(
            f"/api/v1/admin/users/{user_id}/ban",
            headers=headers,
            json={"reason": "测试封禁"},
        )
        assert ban.status_code == 200, ban.text
        assert ban.json()["data"]["status"] == "banned"

        banned_login = client.post("/api/v1/auth/login", json={"username": "admin_api_user", "password": "new-pass-123"})
        assert banned_login.status_code == 403, banned_login.text

        unban = client.post(
            f"/api/v1/admin/users/{user_id}/unban",
            headers=headers,
            json={"reason": "测试解封"},
        )
        assert unban.status_code == 200, unban.text
        assert unban.json()["data"]["status"] == "active"

        user_login = client.post("/api/v1/auth/login", json={"username": "admin_api_user", "password": "new-pass-123"})
        assert user_login.status_code == 200, user_login.text

        sessions = client.get("/api/v1/admin/sessions", headers=headers)
        assert sessions.status_code == 200, sessions.text
        assert sessions.json()["data"]["total"] >= 1

        dissolve = client.post(
            "/api/v1/admin/sessions/1/dissolve",
            headers=headers,
            json={"reason": "测试强制解散"},
        )
        assert dissolve.status_code == 200, dissolve.text
        assert dissolve.json()["data"]["status"] == "archived"

        logs = client.get("/api/v1/admin/operation-logs", headers=headers)
        assert logs.status_code == 200, logs.text
        assert logs.json()["data"]["total"] >= 5

    print("admin api ok")


if __name__ == "__main__":
    main()

"""规则书/模组提取 Agent 验证脚本。"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_content_extract.db")

from httpx import ASGITransport, AsyncClient

from backend.app.db.init_db import reset_demo_db
from backend.app.main import app

PHB = Path(r"C:\Users\congw\Downloads\5eDnD_玩家手册PHB_中译v1.6版_可复制文本.docx")
KRENKO = Path(r"C:\Users\congw\Downloads\追捕克仑可_Krenkos_Way_可复制文本 (1).docx")


async def main() -> None:
    reset_demo_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        if PHB.exists():
            r = await client.post(
                "/api/v1/content/rulebook/extract",
                json={"file_path": str(PHB), "world_id": 1, "focus": "lite_dnd"},
            )
            assert r.status_code == 200, r.text
            data = r.json()["data"]
            assert data["pack_id"] > 0
            assert data["output"]["world_setting"]
            assert data["output"]["world_style"]
            assert len(data["output"]["public_world_facts"]) >= 1
            print(f"[OK] RulebookExtractor pack_id={data['pack_id']} facts={len(data['output']['public_world_facts'])}")
        else:
            print("[SKIP] PHB docx not found")

        if KRENKO.exists():
            r = await client.post(
                "/api/v1/content/module/extract",
                json={
                    "file_path": str(KRENKO),
                    "world_id": 2,
                    "module_title": "追捕克仑可",
                },
            )
            assert r.status_code == 200, r.text
            data = r.json()["data"]
            out = data["output"]
            assert data["module_id"] > 0
            assert out["scenes"]
            assert out["current_scene"]
            assert out["hidden_truths"]
            assert out["story_summary"]
            print(f"[OK] ModuleExtractor module_id={data['module_id']} scenes={len(out['scenes'])}")
        else:
            print("[SKIP] Krenko docx not found")

        if KRENKO.exists():
            r = await client.post(
                "/api/v1/sessions/start",
                json={"world_id": 2, "character_id": 1},
            )
            assert r.status_code == 200, r.text
            session_id = r.json()["data"]["session"]["id"]
            r2 = await client.post(
                f"/api/v1/sessions/{session_id}/action",
                json={"action_text": "我想先观察周围环境，寻找可疑线索。"},
            )
            assert r2.status_code == 200, r2.text
            print(f"[OK] session with module pack session_id={session_id}")

    print("\n=== 内容提取 Agent 验证完成 ===")


if __name__ == "__main__":
    asyncio.run(main())

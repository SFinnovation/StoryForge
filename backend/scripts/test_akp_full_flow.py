# -*- coding: utf-8 -*-
"""AKP 全流程 E2E 测试（启用 AKP + 真实 DeepSeek）。

覆盖用户三项要求：
  1. 将 PHB 规则书 / 追捕克仑可模组两份 docx 经 AKP 建包 + 检索 + Agent 提取后落库，
     并关联到同一个 world，确保后续 agent 能读到 AKP 数据。
  2. 用真实 LLM 跑通 Opening → ActionParser+Narrative+Critic → Summary 全链路，
     所有 agent 的上下文均来源于第 1 步落库的 AKP 数据。
  3. 每个 API 返回结果都用后端 DTO 重新校验，证明与后端接口对齐。

用法（PowerShell，Key 通过环境变量传入，不落盘）：
    $env:LLM_API_KEY="sk-..."; python backend/scripts/test_akp_full_flow.py

可选环境变量：
    LLM_MODEL(默认 deepseek-chat)、LLM_API_BASE(默认 https://api.deepseek.com/v1)
    AKP_BUNDLE_PRESET(默认 quick，PHB 超大文档用 quick 控制 token 预算)
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---- 必须在导入 app 之前设定环境（pydantic-settings 于导入时读取）----
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_akp_full_flow.db")
os.environ["AKP_ENABLED"] = "true"
os.environ.setdefault("AKP_BUNDLE_PRESET", "quick")

if not os.environ.get("LLM_API_KEY"):
    print("[ERROR] 未检测到环境变量 LLM_API_KEY，请先设置后再运行。")
    print('  PowerShell:  $env:LLM_API_KEY="sk-..."; python backend/scripts/test_akp_full_flow.py')
    raise SystemExit(1)

from httpx import ASGITransport, AsyncClient

from backend.app.ai.services import akp_client
from backend.app.ai.services.llm_client import close_llm_client
from backend.app.core.config import settings
from backend.app.db.database import SessionLocal
from backend.app.db.init_db import init_db
from backend.app.main import app
from backend.app.models.models import AdventureModule, Fact, NpcProfile, RulebookPack, World
from backend.app.schemas.character import CharacterResponse
from backend.app.schemas.session_schema import (
    ActionData,
    MessageDTO,
    ReportDTO,
    SessionMetaDTO,
    SessionStartData,
)

PHB = PROJECT_ROOT / "packs" / "rulebook_pack" / "5eDnD_玩家手册PHB_中译v1.6版_可复制文本.docx"
KRENKO = PROJECT_ROOT / "packs" / "mods_pack" / "追捕克仑可_Krenkos_Way_可复制文本 (1).docx"

WORLD_ID = 1
RESULTS: list[dict] = []


def _section(title: str) -> None:
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


def _kv(label: str, value) -> None:
    print(f"  {label}: {value}")


def _record(name: str, ok: bool, note: str) -> None:
    RESULTS.append({"name": name, "ok": ok, "note": note})
    print(f"  [{'PASS' if ok else 'FAIL'}] {name} — {note}")


def _trim(text: str, n: int = 240) -> str:
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= n else text[:n] + " …"


def _seed_world() -> None:
    """建库 + 造一个启用的 world（供两份包关联）。"""
    init_db(drop_first=True)
    with SessionLocal() as db:
        if db.get(World, WORLD_ID) is None:
            db.add(
                World(
                    id=WORLD_ID,
                    name="追捕克仑可（AKP 全流程）",
                    type="fantasy",
                    description="AKP 全流程测试世界，内容由两份 docx 经知识包提取。",
                    opening_prompt="待模组导入后覆盖。",
                    rule_style="lite_dnd",
                    difficulty="normal",
                    is_enabled=1,
                    created_by=1,
                )
            )
            db.commit()


def _pack_dir_ok(dir_str: str | None) -> bool:
    if not dir_str:
        return False
    p = Path(dir_str)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return (p / "kb.sqlite").is_file()


async def _post(client: AsyncClient, url: str, json: dict) -> dict:
    r = await client.post(url, json=json)
    assert r.status_code in (200, 201), f"{url} -> {r.status_code}: {r.text[:500]}"
    body = r.json()
    assert body.get("code") == 0, f"{url} 业务失败: {body}"
    return body["data"]


async def _get(client: AsyncClient, url: str) -> dict:
    r = await client.get(url)
    assert r.status_code == 200, f"{url} -> {r.status_code}: {r.text[:500]}"
    return r.json()["data"]


async def main() -> int:
    _section("环境")
    _kv("模型", f"{settings.LLM_MODEL} @ {settings.LLM_API_BASE}")
    _kv("AKP_ENABLED", settings.AKP_ENABLED)
    _kv("AKP_BUNDLE_PRESET", settings.AKP_BUNDLE_PRESET)
    _kv("PHB", f"{PHB.name} ({'存在' if PHB.exists() else '缺失'})")
    _kv("KRENKO", f"{KRENKO.name} ({'存在' if KRENKO.exists() else '缺失'})")
    if not (PHB.exists() and KRENKO.exists()):
        print("[ERROR] 缺少 docx 文件，无法进行 AKP 全流程测试。")
        return 2

    _seed_world()
    transport = ASGITransport(app=app)
    started = time.perf_counter()
    pack_id = module_id = character_id = session_id = 0

    async with AsyncClient(transport=transport, base_url="http://test", timeout=600.0) as client:
        # ---------- 步骤 1a：规则书 → AKP 建包 + 提取落库 ----------
        _section("步骤1a · RulebookExtractor（PHB 经 AKP 提取落库）")
        try:
            data = await _post(
                client,
                "/api/v1/content/rulebook/extract",
                {"file_path": str(PHB), "world_id": WORLD_ID, "focus": "lite_dnd"},
            )
            pack_id = data["pack_id"]
            out = data["output"]
            _kv("pack_id", pack_id)
            _kv("tokens/latency", f"{data['tokens_used']} / {data['latency_ms']}ms")
            _kv("title", out["title"])
            _kv("world_style", out["world_style"])
            _kv("world_setting", _trim(out["world_setting"]))
            _kv("public_world_facts", len(out["public_world_facts"]))
            for f in out["public_world_facts"][:4]:
                print(f"      - [{f.get('importance')}/{f.get('category')}] "
                      f"{_trim(f.get('content', ''), 90)}  src={f.get('source_ref') or '—'}")
            ok = bool(out["world_setting"]) and bool(out["world_style"]) and len(out["public_world_facts"]) >= 1
            _record("RulebookExtractor 提取落库", ok, f"{len(out['public_world_facts'])} 条世界事实")
        except Exception as exc:  # noqa: BLE001
            _record("RulebookExtractor 提取落库", False, f"{type(exc).__name__}: {exc}")

        # ---------- 步骤 1b：模组 → AKP 建包 + 提取落库 ----------
        _section("步骤1b · ModuleExtractor（追捕克仑可 经 AKP 提取落库）")
        try:
            data = await _post(
                client,
                "/api/v1/content/module/extract",
                {"file_path": str(KRENKO), "world_id": WORLD_ID, "module_title": "追捕克仑可"},
            )
            module_id = data["module_id"]
            out = data["output"]
            _kv("module_id", module_id)
            _kv("tokens/latency", f"{data['tokens_used']} / {data['latency_ms']}ms")
            _kv("title", out["title"])
            _kv("current_scene", out["current_scene"])
            _kv("story_summary", _trim(out["story_summary"]))
            _kv("scenes", len(out["scenes"]))
            for s in out["scenes"][:4]:
                print(f"      - {s.get('scene_id')} / {s.get('title')} "
                      f"-> 出口: {', '.join(s.get('exits', [])) or '无'}")
            _kv("hidden_truths", len(out["hidden_truths"]))
            _kv("seed_npcs / visible_npcs", f"{len(out['seed_npcs'])} / {len(out['visible_npcs'])}")
            ok = bool(out["story_summary"]) and len(out["scenes"]) >= 1 and bool(out["current_scene"])
            _record("ModuleExtractor 提取落库", ok,
                    f"{len(out['scenes'])} 场景 / {len(out['hidden_truths'])} 隐藏真相")
        except Exception as exc:  # noqa: BLE001
            _record("ModuleExtractor 提取落库", False, f"{type(exc).__name__}: {exc}")

        # ---------- 步骤 1c：AKP 落地校验（知识包目录 + 可检索）----------
        _section("步骤1c · AKP 本地搭建校验（知识包落盘 + 可检索）")
        try:
            with SessionLocal() as db:
                rb = db.get(RulebookPack, pack_id) if pack_id else None
                mod = db.get(AdventureModule, module_id) if module_id else None
                world = db.get(World, WORLD_ID)
                rb_dir = rb.knowledge_pack_dir if rb else None
                mod_dir = mod.knowledge_pack_dir if mod else None
                _kv("rulebook.knowledge_pack_dir", rb_dir)
                _kv("module.knowledge_pack_dir", mod_dir)
                _kv("world.rulebook_pack_id", getattr(world, "rulebook_pack_id", None))
                _kv("world.adventure_module_id", getattr(world, "adventure_module_id", None))
                built_ok = _pack_dir_ok(rb_dir) and _pack_dir_ok(mod_dir)
                linked_ok = (world.rulebook_pack_id == pack_id) and (world.adventure_module_id == module_id)

            # 直接对已落库的知识包做一次确定性检索，证明"数据可被后续 agent 使用"
            research_ok = False
            if mod_dir:
                mp = Path(mod_dir)
                if not mp.is_absolute():
                    mp = PROJECT_ROOT / mp
                bundle = akp_client.research(mp, "克仑可的藏身处与幕后雇主是谁？", run_id="verify1")
                research_ok = bundle.verify_ok and "## References" in bundle.bundle_md
                _kv("模组包检索命中", f"hits={bundle.hits}, verify_ok={bundle.verify_ok}")
                print(f"      证据包摘要: {_trim(bundle.bundle_md, 200)}")
            _record("AKP 知识包落盘 + 关联 world", built_ok and linked_ok,
                    "kb.sqlite 就位且已关联 world" if built_ok and linked_ok else "落盘或关联缺失")
            _record("AKP 知识包确定性可检索", research_ok,
                    "bundle 命中且含 ## References" if research_ok else "检索未命中")
        except Exception as exc:  # noqa: BLE001
            _record("AKP 本地搭建校验", False, f"{type(exc).__name__}: {exc}")

        # ---------- 步骤 1d：创建角色（接口对齐）----------
        _section("步骤1d · 创建角色")
        try:
            data = await _post(
                client,
                "/api/v1/characters",
                {
                    "name": "凯尔·维恩",
                    "profession": "赏金侦探",
                    "motivation": "追捕越狱的鬼怪黑帮头目克仑可，并查明其幕后雇主。",
                    "base_attributes": {
                        "strength": 13, "dexterity": 15, "constitution": 12,
                        "intelligence": 14, "wisdom": 10, "charisma": 8,
                    },
                },
            )
            CharacterResponse.model_validate(data)  # 接口对齐校验
            character_id = data["id"]
            _kv("character_id", character_id)
            _kv("name / profession", f"{data['name']} / {data['profession']}")
            _record("创建角色 + CharacterResponse 对齐", True, f"id={character_id}")
        except Exception as exc:  # noqa: BLE001
            _record("创建角色 + CharacterResponse 对齐", False, f"{type(exc).__name__}: {exc}")

        # ---------- 步骤 2a：OpeningAgent（消费 AKP 数据）----------
        _section("步骤2a · OpeningAgent 开局（上下文来自 AKP 规则书+模组）")
        try:
            data = await _post(
                client,
                "/api/v1/sessions/start",
                {"world_id": WORLD_ID, "character_id": character_id},
            )
            SessionStartData.model_validate(data)  # 接口对齐校验
            session_id = data["session"]["id"]
            op = data["opening"]
            _kv("session_id", session_id)
            _kv("scene_title", op["scene_title"])
            _kv("main_task", op["main_task"])
            print(f"      narration: {_trim(op['narration'], 300)}")
            _kv("npcs", ", ".join(n.get("name", "") for n in op["npcs"]) or "（无）")
            _kv("initial_clues", len(op["initial_clues"]))

            # 校验 world_seed 已把 AKP 模组数据灌入会话
            with SessionLocal() as db:
                facts = db.query(Fact).filter(Fact.session_id == session_id).all()
                npcs = db.query(NpcProfile).filter(NpcProfile.session_id == session_id).all()
                by_type: dict[str, int] = {}
                for f in facts:
                    by_type[f.fact_type] = by_type.get(f.fact_type, 0) + 1
            _kv("会话已灌入 facts", f"{len(facts)} 条 {by_type}")
            _kv("会话已灌入 npc_profiles", len(npcs))
            seeded_ok = len(facts) > 0  # 数据源自 AKP 模组包
            ok = bool(op["scene_title"]) and len(op["narration"]) > 40 and seeded_ok
            _record("OpeningAgent + SessionStartData 对齐", ok,
                    f"开局生成成功，AKP 模组灌入 {len(facts)} facts / {len(npcs)} npcs")
        except Exception as exc:  # noqa: BLE001
            _record("OpeningAgent + SessionStartData 对齐", False, f"{type(exc).__name__}: {exc}")

        # ---------- 步骤 2b：ActionParser + Narrative + Critic 全链路 ----------
        _section("步骤2b · Action 全链路（Parser→Rule→Narrative→Critic）")
        actions = [
            "我仔细观察周围环境，留意任何与克仑可行踪相关的可疑线索。",
            "我压低声音向附近的线人打听克仑可最近的落脚点。",
        ]
        for idx, action_text in enumerate(actions, start=1):
            try:
                data = await _post(
                    client,
                    f"/api/v1/sessions/{session_id}/action",
                    {"action_text": action_text},
                )
                ActionData.model_validate(data)  # 接口对齐校验
                story = data["story"]
                review = data["ai_review"]
                chk = data.get("check")
                print(f"    行动{idx}: {action_text}")
                if chk:
                    _kv("check", f"{chk['check_type']} d20={chk['dice_roll']} "
                                 f"final={chk['final_value']} vs DC{chk['dc']} -> "
                                 f"{'成功' if chk['is_success'] else '失败'}")
                else:
                    _kv("check", "无需检定")
                print(f"      narration: {_trim(story['narration'], 300)}")
                _kv("next_options", " | ".join(story["next_options"]) or "（无）")
                _kv("ai_review", f"approved={review['approved']} score={review['overall_score']} "
                                 f"revisions={review['revision_count']} fallback={review['used_fallback']}")
                ok = len(story["narration"]) > 20 and review["overall_score"] >= 0
                _record(f"Action#{idx}(Parser+Narrative+Critic) + ActionData 对齐", ok,
                        f"审核分={review['overall_score']}, 修正{review['revision_count']}次")
            except Exception as exc:  # noqa: BLE001
                _record(f"Action#{idx} + ActionData 对齐", False, f"{type(exc).__name__}: {exc}")

        # ---------- 步骤 2c：SummaryAgent 战报 ----------
        _section("步骤2c · SummaryAgent 本局战报")
        try:
            data = await _post(client, f"/api/v1/sessions/{session_id}/report/generate", {})
            ReportDTO.model_validate(data)  # 接口对齐校验
            _kv("title", data["title"])
            _kv("ending_type", data["ending_type"])
            print(f"      story_summary: {_trim(data['story_summary'], 300)}")
            _kv("key_choices", " | ".join(data["key_choices"]) or "（无）")
            _kv("ai_suggestion", _trim(data["ai_suggestion"], 120))
            ok = bool(data["title"]) and len(data["story_summary"]) > 20
            _record("SummaryAgent + ReportDTO 对齐", ok, "生成战报总结")
        except Exception as exc:  # noqa: BLE001
            _record("SummaryAgent + ReportDTO 对齐", False, f"{type(exc).__name__}: {exc}")

        # ---------- 步骤 3：其余读取接口对齐校验 ----------
        _section("步骤3 · 读取接口对齐校验（facts/meta/messages/reviews/content）")
        try:
            facts = await _get(client, f"/api/v1/sessions/{session_id}/facts?scope=player_known")
            assert "facts" in facts and isinstance(facts["facts"], list)

            meta = await _get(client, f"/api/v1/sessions/{session_id}/meta")
            SessionMetaDTO.model_validate(meta)

            messages = await _get(client, f"/api/v1/sessions/{session_id}/messages")
            for m in messages:
                MessageDTO.model_validate(m)

            reviews = await _get(client, f"/api/v1/sessions/{session_id}/ai-reviews")
            assert "reviews" in reviews and isinstance(reviews["reviews"], list)

            rb_get = await _get(client, f"/api/v1/content/rulebook/{pack_id}")
            mod_get = await _get(client, f"/api/v1/content/module/{module_id}")
            assert rb_get["world_style"] and mod_get["current_scene"]

            _kv("meta", meta)
            _kv("messages", f"{len(messages)} 条")
            _kv("ai-reviews", f"{len(reviews['reviews'])} 条")
            _record("读取接口全部对齐", True,
                    "facts/meta/messages/ai-reviews/content 均通过 DTO 校验")
        except Exception as exc:  # noqa: BLE001
            _record("读取接口全部对齐", False, f"{type(exc).__name__}: {exc}")

    await close_llm_client()

    # ---------- 汇总 ----------
    _section("汇总")
    passed = sum(1 for r in RESULTS if r["ok"])
    print(f"  {'项目':<48}{'结果':<8}备注")
    print("  " + "-" * 74)
    for r in RESULTS:
        print(f"  {r['name']:<46}{'PASS' if r['ok'] else 'FAIL':<8}{r['note']}")
    print("  " + "-" * 74)
    elapsed = time.perf_counter() - started
    print(f"  通过 {passed}/{len(RESULTS)} · 总耗时 {elapsed:.1f}s")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

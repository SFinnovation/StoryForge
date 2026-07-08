"""AI 模块接口性能基准 — mock 路径（无 LLM 调用）。"""

from __future__ import annotations

import asyncio
import statistics
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.ai import get_ai_module
from backend.app.ai.schemas import (
    ActionParseInput,
    CharacterCard,
    CheckResult,
    NarrativeInput,
    OpeningInput,
    SummaryInput,
)
from backend.app.schemas.action_schema import ActionRequest
from backend.app.services.action_service import handle_action
from backend.app.db.database import SessionLocal


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(len(ordered) * p / 100)
    return ordered[min(idx, len(ordered) - 1)]


def stats(name: str, samples_ms: list[float]) -> None:
    print(
        f"{name:32} "
        f"min={min(samples_ms):.2f}ms "
        f"p50={statistics.median(samples_ms):.2f}ms "
        f"p95={percentile(samples_ms, 95):.2f}ms "
        f"max={max(samples_ms):.2f}ms "
        f"avg={statistics.mean(samples_ms):.2f}ms"
    )


async def bench_ai_once(ai, character) -> dict[str, float]:
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    await ai.generate_opening(OpeningInput(world="古堡悬疑", character=character))
    timings["opening"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    parsed = await ai.parse_action(
        ActionParseInput(
            player_action="我想先观察大厅，看看有没有异常线索。",
            current_scene="黑鸦古堡大厅",
            character=character,
        )
    )
    timings["parse_action"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    await ai.generate_narrative(
        NarrativeInput(
            player_action="我想先观察大厅，看看有没有异常线索。",
            check_result=CheckResult(success=False, dice_roll=9, final_value=11, dc=12),
            current_scene="黑鸦古堡大厅",
            clue_pressure=0.2,
            world="古堡悬疑",
            character=character,
        )
    )
    timings["narrative_with_critic"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    await ai.generate_summary(
        SummaryInput(
            world="古堡悬疑",
            character=character,
            player_actions=["观察大厅"],
            check_results=[CheckResult(success=False, dice_roll=9, final_value=11, dc=12)],
            ai_narrations=["mock narration"],
            discovered_clues=[],
        )
    )
    timings["summary"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    _ = parsed.output.model_dump_json()
    timings["schema_serialize"] = (time.perf_counter() - t0) * 1000

    timings["full_action_flow"] = timings["parse_action"] + timings["narrative_with_critic"]
    return timings


async def bench_action_service_once(session_id: int) -> float:
    t0 = time.perf_counter()
    with SessionLocal() as db:
        await handle_action(db, session_id, 1, "我想先观察大厅，看看有没有异常线索。")
    return (time.perf_counter() - t0) * 1000


async def main() -> None:
    ai = get_ai_module()
    character = CharacterCard(
        name="艾琳",
        profession="调查员",
        background="研究失踪案件的年轻侦探",
        motivation="寻找失踪学者留下的最后一份手稿",
    )

    rounds = 50
    buckets: dict[str, list[float]] = {}

    await bench_ai_once(ai, character)
    for _ in range(rounds):
        result = await bench_ai_once(ai, character)
        for key, value in result.items():
            buckets.setdefault(key, []).append(value)

    print(f"=== AI 模块接口性能（mock，{rounds} 轮）===\n")
    for key in [
        "opening",
        "parse_action",
        "narrative_with_critic",
        "summary",
        "full_action_flow",
        "schema_serialize",
    ]:
        stats(key, buckets[key])

    service_samples: list[float] = []
    # action_service 基准需要先创建会话，此处跳过（见 verify_implementation_spec.py）
    print("\n=== action_service 端到端 ===")
    print("(跳过 — 请运行 scripts/verify_implementation_spec.py)")

    print("\n=== 单例复用验证 ===")
    ai2 = get_ai_module()
    print(f"get_ai_module() 同一实例: {ai is ai2}")


if __name__ == "__main__":
    asyncio.run(main())

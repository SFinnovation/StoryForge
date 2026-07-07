"""AI 模块本地联调脚本（无需 LLM API Key 时使用 mock 响应）。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ai import get_ai_module
from app.ai.schemas import (
    ActionParseInput,
    CharacterCard,
    CheckResult,
    NarrativeInput,
    OpeningInput,
    SummaryInput,
)


async def main() -> None:
    ai = get_ai_module()
    character = CharacterCard(
        name="艾琳",
        profession="调查员",
        background="研究失踪案件的年轻侦探",
        motivation="寻找失踪学者留下的最后一份手稿",
    )

    print("=== 1. OpeningAgent ===")
    opening = await ai.generate_opening(OpeningInput(world="古堡悬疑", character=character))
    print(opening.output.display_text[:200], "...")
    print(f"metrics: tokens={opening.tokens_used}, latency={opening.latency_ms}ms\n")

    print("=== 2. ActionParserAgent ===")
    parsed = await ai.parse_action(
        ActionParseInput(
            player_action="我想先观察大厅，看看有没有异常线索。",
            current_scene="黑鸦古堡大厅",
            character=character,
        )
    )
    print(parsed.output.model_dump_json(indent=2, ensure_ascii=False))
    print(f"metrics: tokens={parsed.tokens_used}, latency={parsed.latency_ms}ms\n")

    print("=== 3. NarrativeAgent + CriticAgent ===")
    story = await ai.generate_narrative(
        NarrativeInput(
            player_action="我想先观察大厅，看看有没有异常线索。",
            check_result=CheckResult(success=False, dice_roll=9, final_value=11, dc=12),
            current_scene="黑鸦古堡大厅",
            known_clues=[],
            clue_pressure=0.2,
            world="古堡悬疑",
            character=character,
        )
    )
    print(story.display_text[:200], "...")
    print("review:", story.review.model_dump_json(indent=2, ensure_ascii=False))
    print(f"metrics: tokens={story.tokens_used}, latency={story.latency_ms}ms\n")

    print("=== 4. SummaryAgent ===")
    summary = await ai.generate_summary(
        SummaryInput(
            world="古堡悬疑",
            character=character,
            player_actions=["观察大厅", "询问管家"],
            check_results=[CheckResult(success=False, dice_roll=9, final_value=11, dc=12)],
            ai_narrations=[story.display_text],
            discovered_clues=["钟摆停止"],
        )
    )
    print(summary.output.display_text[:200], "...")
    print(f"metrics: tokens={summary.tokens_used}, latency={summary.latency_ms}ms")


if __name__ == "__main__":
    asyncio.run(main())

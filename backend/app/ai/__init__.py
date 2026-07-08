"""
StoryForge AI 模块 — 双 Agent 架构

后端调用示例::

    from backend.app.ai import get_ai_module
    from backend.app.ai.schemas import OpeningInput, ActionParseInput, NarrativeInput, SummaryInput
    from backend.app.ai.schemas import CharacterCard, CheckResult

    ai = get_ai_module()

    opening = await ai.generate_opening(
        OpeningInput(
            world="古堡悬疑",
            character=CharacterCard(
                name="艾琳",
                profession="调查员",
                background="研究失踪案件的年轻侦探",
                motivation="寻找失踪学者留下的最后一份手稿",
            ),
        )
    )

    parsed = await ai.parse_action(
        ActionParseInput(
            player_action="我想先观察大厅，看看有没有异常线索。",
            current_scene="黑鸦古堡大厅",
        )
    )

    story = await ai.generate_narrative(
        NarrativeInput(
            player_action="我想先观察大厅，看看有没有异常线索。",
            check_result=CheckResult(success=False, dice_roll=9, final_value=11, dc=12),
            current_scene="黑鸦古堡大厅",
            clue_pressure=0.2,
        )
    )
"""

from backend.app.ai.orchestrator import AIModule, get_ai_module

__all__ = ["AIModule", "get_ai_module"]

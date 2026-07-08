from __future__ import annotations

from app.ai.schemas.character import WorldContext
from app.ai.schemas.narrative import NarrativeInput, NarrativeOutput
from app.ai.services.fallbacks import mock_narrative
from app.ai.services.json_utils import dumps_context, parse_model
from app.ai.services.llm_client import LLMResponse, get_llm_client
from app.ai.services.prompt_loader import load_prompt, render_prompt


class NarrativeAgent:
    """主叙事 Agent — 根据后端判定结果生成剧情。"""

    async def generate(self, data: NarrativeInput) -> tuple[NarrativeOutput, LLMResponse | None]:
        return await self._run(data, revise=False)

    async def revise(self, data: NarrativeInput) -> tuple[NarrativeOutput, LLMResponse | None]:
        return await self._run(data, revise=True)

    async def _run(
        self, data: NarrativeInput, *, revise: bool
    ) -> tuple[NarrativeOutput, LLMResponse | None]:
        client = get_llm_client()
        if not client.enabled:
            return mock_narrative(data), None

        world_style = ""
        if data.world:
            world = data.world if isinstance(data.world, WorldContext) else WorldContext(name=data.world)
            world_style = world.name

        template = load_prompt("narrative_agent.txt")
        user_content = render_prompt(
            template,
            world_style=world_style or "奇幻悬疑",
            public_world_facts=dumps_context(data.public_world_facts),
            current_scene=data.current_scene or "未知场景",
            player_card=dumps_context(data.character or {}),
            recent_summary=data.recent_summary or "（无）",
            player_known_clues=dumps_context(data.known_clues),
            visible_npcs=dumps_context(data.visible_npcs),
            player_action=data.player_action,
            rule_result=dumps_context(data.check_result or {"needs_check": False}),
            clue_pressure=str(data.clue_pressure),
        )
        if revise and data.revision_instructions:
            user_content += "\n\n【审核修正要求】\n" + "\n".join(
                f"- {item}" for item in data.revision_instructions
            )
        if revise and data.previous_narration:
            user_content += f"\n\n【上一轮被驳回的叙事】\n{data.previous_narration}"

        system = (
            "你是 StoryForge NarrativeAgent。"
            "骰子结果由后端给定，不得修改 success/failure。"
            "只输出 JSON。"
        )
        llm = await client.chat(system, user_content)
        output = parse_model(llm.content, NarrativeOutput)
        return output, llm

from __future__ import annotations

from backend.app.ai.schemas.character import WorldContext
from backend.app.ai.schemas.summary import SummaryInput, SummaryOutput
from backend.app.ai.services.fallbacks import mock_summary
from backend.app.ai.services.json_utils import dumps_context, parse_model
from backend.app.ai.services.llm_client import LLMResponse, get_llm_client
from backend.app.ai.services.prompt_loader import load_prompt, render_prompt


class SummaryAgent:
    """本局总结 Agent。"""

    async def generate(self, data: SummaryInput) -> tuple[SummaryOutput, LLMResponse | None]:
        client = get_llm_client()
        if not client.enabled:
            return mock_summary(data), None

        world_ctx = (
            data.world
            if isinstance(data.world, WorldContext)
            else WorldContext(name=str(data.world))
        )
        template = load_prompt("report.txt")
        user_content = render_prompt(
            template,
            world_setting=dumps_context(world_ctx),
            player_card=dumps_context(data.character),
            player_actions=dumps_context(data.player_actions),
            check_results=dumps_context([c.model_dump() for c in data.check_results]),
            ai_narrations=dumps_context(data.ai_narrations),
            discovered_clues=dumps_context(data.discovered_clues),
            task_status=dumps_context(data.task_status),
            session_summary=data.session_summary or "（无）",
        )
        system = "你是 StoryForge SummaryAgent。只输出 JSON。"
        llm = await client.chat(system, user_content, temperature=0.5)
        output = parse_model(llm.content, SummaryOutput)
        return output, llm

from __future__ import annotations

from app.ai.schemas.opening import OpeningInput, OpeningOutput
from app.ai.services.fallbacks import mock_opening
from app.ai.services.json_utils import dumps_context, parse_model
from app.ai.services.llm_client import LLMResponse, get_llm_client
from app.ai.services.prompt_loader import load_prompt, render_prompt


class OpeningAgent:
    """开局剧情生成 Agent。"""

    async def generate(self, data: OpeningInput) -> tuple[OpeningOutput, LLMResponse | None]:
        client = get_llm_client()
        if not client.enabled:
            return mock_opening(data), None

        world = data.resolved_world()
        template = load_prompt("opening.txt")
        user_content = render_prompt(
            template,
            world_setting=dumps_context(
                {
                    "name": world.name,
                    "description": world.description,
                    "style": world.style,
                    "opening_prompt": world.opening_prompt,
                }
            ),
            player_card=dumps_context(data.character),
            public_world_facts=dumps_context(data.public_world_facts),
            seed_npcs=dumps_context([n.model_dump() for n in data.seed_npcs]),
        )
        system = "你是 StoryForge OpeningAgent。严格输出 JSON，不要输出 markdown 代码块以外的内容。"
        llm = await client.chat(system, user_content)
        output = parse_model(llm.content, OpeningOutput)
        return output, llm

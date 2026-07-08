# -*- coding: utf-8 -*-
"""GuidanceAgent — 回答 dm.ask，低泄露、不剧透、不推进剧情。"""
from __future__ import annotations

from backend.app.ai.schemas.guidance import GuidanceInput, GuidanceOutput
from backend.app.ai.services.fallbacks import mock_guidance
from backend.app.ai.services.json_utils import dumps_context, parse_model
from backend.app.ai.services.llm_client import LLMResponse, get_llm_client
from backend.app.ai.services.prompt_loader import load_prompt, render_prompt


class GuidanceAgent:
    async def generate(self, data: GuidanceInput) -> tuple[GuidanceOutput, LLMResponse | None]:
        client = get_llm_client()
        if not client.enabled:
            return mock_guidance(data), None

        template = load_prompt("guidance_agent.txt")
        user_content = render_prompt(
            template,
            world_setting=dumps_context(
                {
                    "name": data.world.name,
                    "description": data.world.description,
                    "style": data.world.style,
                }
            ),
            current_scene=data.current_scene or "（尚未开局）",
            current_task=data.current_task or "（暂无）",
            player_card=dumps_context(data.character),
            known_clues=dumps_context(data.known_clues),
            public_world_facts=dumps_context(data.public_world_facts),
            visible_npcs=dumps_context(data.visible_npcs),
            active_tasks=dumps_context(data.active_tasks),
            recent_summary=data.recent_summary or "（无）",
            question=data.question,
        )
        system = (
            "你是 StoryForge GuidanceAgent。严格输出 JSON，"
            "不得剧透 hidden_truth，不得替玩家做决定。"
        )
        llm = await client.chat(system, user_content, temperature=0.4)
        output = parse_model(llm.content, GuidanceOutput)
        return output, llm

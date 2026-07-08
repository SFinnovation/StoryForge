from __future__ import annotations

from app.ai.schemas.action_parse import ActionParseInput, ActionParseOutput
from app.ai.services.fallbacks import mock_action_parse
from app.ai.services.json_utils import dumps_context, parse_model
from app.ai.services.llm_client import LLMResponse, get_llm_client
from app.ai.services.prompt_loader import load_prompt, render_prompt


class ActionParserAgent:
    """行动解析 Agent — 理解玩家输入，输出结构化检定建议。"""

    async def parse(self, data: ActionParseInput) -> tuple[ActionParseOutput, LLMResponse | None]:
        client = get_llm_client()
        if not client.enabled:
            return mock_action_parse(data), None

        template = load_prompt("action_parser.txt")
        user_content = render_prompt(
            template,
            current_scene=data.current_scene or "未知场景",
            player_card=dumps_context(data.character or {}),
            recent_summary=data.recent_summary or "（无）",
            player_action=data.player_action,
        )
        system = (
            "你是 StoryForge ActionParserAgent。"
            "只输出 JSON。禁止生成 dice_roll、final_value、is_success。"
        )
        llm = await client.chat(system, user_content, temperature=0.3)
        output = parse_model(llm.content, ActionParseOutput)
        return output, llm

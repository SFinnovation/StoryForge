"""ModuleExtractorAgent — 冒险模组精炼提取。"""

from __future__ import annotations

from app.ai.schemas.module_extract import ModuleExtractionInput, ModuleExtractionOutput
from app.ai.services.fallbacks import mock_module_extract
from app.ai.services.json_utils import parse_model
from app.ai.services.llm_client import LLMResponse, get_llm_client
from app.ai.services.prompt_loader import load_prompt, render_prompt
from app.ai.services.text_chunker import truncate_for_llm


class ModuleExtractorAgent:
    async def extract(
        self, data: ModuleExtractionInput
    ) -> tuple[ModuleExtractionOutput, LLMResponse | None]:
        client = get_llm_client()
        if not client.enabled:
            return mock_module_extract(data), None

        module_text = truncate_for_llm(data.raw_text, max_chars=18000)
        template = load_prompt("module_extractor.txt")
        user_content = render_prompt(
            template,
            source_name=data.source_name,
            module_title=data.module_title or data.source_name,
            module_text=module_text,
        )
        system = "你是 StoryForge ModuleExtractorAgent。只输出 JSON。"
        llm = await client.chat(system, user_content, temperature=0.3, max_tokens=4096)
        output = parse_model(llm.content, ModuleExtractionOutput)
        return output, llm

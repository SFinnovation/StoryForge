"""RulebookExtractorAgent — 规则书提取、压缩、标准化。"""

from __future__ import annotations

from backend.app.ai.schemas.rulebook_extract import RulebookExtractionInput, RulebookExtractionOutput
from backend.app.ai.services.fallbacks import mock_rulebook_extract
from backend.app.ai.services.json_utils import dumps_context, parse_model
from backend.app.ai.services.llm_client import LLMResponse, get_llm_client
from backend.app.ai.services.prompt_loader import load_prompt, render_prompt
from backend.app.ai.services.text_chunker import chunk_text, select_rulebook_sections


class RulebookExtractorAgent:
    async def extract(
        self, data: RulebookExtractionInput
    ) -> tuple[RulebookExtractionOutput, LLMResponse | None]:
        client = get_llm_client()
        if not client.enabled:
            return mock_rulebook_extract(data), None

        # AKP 模式：有证据包时，直接基于带出处的证据提炼（跳过关键词筛选/分块）。
        if data.evidence_bundles:
            return await self._extract_from_bundles(data)

        focused = select_rulebook_sections(data.raw_text)
        chunks = chunk_text(focused, chunk_size=6000)

        if len(chunks) == 1:
            return await self._extract_chunk(data.source_name, data.focus, chunks[0])

        partials: list[RulebookExtractionOutput] = []
        tokens = 0
        latency = 0
        for i, chunk in enumerate(chunks[:6]):
            out, llm = await self._extract_chunk(
                f"{data.source_name}#part{i + 1}",
                data.focus,
                chunk,
            )
            partials.append(out)
            if llm:
                tokens += llm.tokens_used
                latency += llm.latency_ms

        merged, merge_llm = await self._consolidate(data.source_name, partials)
        if merge_llm:
            tokens += merge_llm.tokens_used
            latency += merge_llm.latency_ms
        return merged, LLMResponse(content="", tokens_used=tokens, latency_ms=latency)

    async def _extract_from_bundles(
        self, data: RulebookExtractionInput
    ) -> tuple[RulebookExtractionOutput, LLMResponse | None]:
        client = get_llm_client()
        template = load_prompt("rulebook_extractor_bundle.txt")
        evidence = "\n\n---\n\n".join(data.evidence_bundles)
        user_content = render_prompt(
            template,
            source_name=data.source_name,
            focus=data.focus,
            evidence=evidence,
        )
        system = "你是 StoryForge RulebookExtractorAgent（证据包模式）。只输出 JSON。"
        llm = await client.chat(system, user_content, temperature=0.2, max_tokens=4000)
        return parse_model(llm.content, RulebookExtractionOutput), llm

    async def _extract_chunk(
        self, source_name: str, focus: str, chunk: str
    ) -> tuple[RulebookExtractionOutput, LLMResponse | None]:
        client = get_llm_client()
        template = load_prompt("rulebook_extractor.txt")
        user_content = render_prompt(
            template,
            source_name=source_name,
            focus=focus,
            text_chunk=chunk,
        )
        system = "你是 StoryForge RulebookExtractorAgent。只输出 JSON。"
        llm = await client.chat(system, user_content, temperature=0.2, max_tokens=3000)
        return parse_model(llm.content, RulebookExtractionOutput), llm

    async def _consolidate(
        self, source_name: str, partials: list[RulebookExtractionOutput]
    ) -> tuple[RulebookExtractionOutput, LLMResponse | None]:
        client = get_llm_client()
        template = load_prompt("rulebook_consolidate.txt")
        user_content = render_prompt(
            template,
            source_name=source_name,
            partial_results=dumps_context([p.model_dump() for p in partials]),
        )
        system = "你是 StoryForge RulebookConsolidatorAgent。只输出 JSON。"
        llm = await client.chat(system, user_content, temperature=0.2, max_tokens=4000)
        return parse_model(llm.content, RulebookExtractionOutput), llm

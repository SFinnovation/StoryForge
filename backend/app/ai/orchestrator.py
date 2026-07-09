from __future__ import annotations

import logging

from backend.app.ai.schemas.action_parse import ActionParseInput, ActionParseOutput
from backend.app.ai.schemas.agent_result import AgentResult
from backend.app.ai.schemas.character import CharacterCard, WorldContext
from backend.app.ai.schemas.guidance import GuidanceInput, GuidanceOutput
from backend.app.ai.schemas.module_extract import ModuleExtractionInput, ModuleExtractionOutput
from backend.app.ai.schemas.narrative import NarrativeInput, NarrativeWithReviewResult
from backend.app.ai.schemas.opening import OpeningInput, OpeningOutput
from backend.app.ai.schemas.rulebook_extract import RulebookExtractionInput, RulebookExtractionOutput
from backend.app.ai.schemas.summary import SummaryInput, SummaryOutput
from backend.app.ai.services.action_parser_agent import ActionParserAgent
from backend.app.ai.services.guidance_agent import GuidanceAgent
from backend.app.ai.services.module_extractor_agent import ModuleExtractorAgent
from backend.app.ai.services.opening_agent import OpeningAgent
from backend.app.ai.services.revision_loop import RevisionLoop
from backend.app.ai.services.rulebook_extractor_agent import RulebookExtractorAgent
from backend.app.ai.services.summary_agent import SummaryAgent
from backend.app.ai.services.fallbacks import (
    mock_action_parse,
    mock_critic_approve,
    mock_guidance,
    mock_module_extract,
    mock_narrative,
    mock_opening,
    mock_rulebook_extract,
    mock_summary,
)

logger = logging.getLogger(__name__)


class AIModule:
    """
    AI 模块统一入口，供后端 session_service / action_service 调用。

    所有方法返回 AgentResult（含 tokens_used / latency_ms），
    generate_narrative 额外返回审核信息。
    """

    def __init__(self) -> None:
        self.opening_agent = OpeningAgent()
        self.action_parser_agent = ActionParserAgent()
        self.revision_loop = RevisionLoop()
        self.summary_agent = SummaryAgent()
        self.guidance_agent = GuidanceAgent()
        self.rulebook_extractor_agent = RulebookExtractorAgent()
        self.module_extractor_agent = ModuleExtractorAgent()

    async def generate_opening(self, data: OpeningInput) -> AgentResult[OpeningOutput]:
        try:
            output, llm = await self.opening_agent.generate(data)
        except Exception as exc:
            logger.warning("OpeningAgent failed; using local fallback opening: %s", exc)
            output = mock_opening(data)
            llm = None
        return AgentResult(
            output=output,
            tokens_used=llm.tokens_used if llm else 0,
            latency_ms=llm.latency_ms if llm else 0,
        )

    async def parse_action(self, data: ActionParseInput) -> AgentResult[ActionParseOutput]:
        try:
            output, llm = await self.action_parser_agent.parse(data)
        except Exception as exc:
            logger.warning("ActionParserAgent failed; using local fallback action parse: %s", exc)
            output = mock_action_parse(data)
            llm = None
        return AgentResult(
            output=output,
            tokens_used=llm.tokens_used if llm else 0,
            latency_ms=llm.latency_ms if llm else 0,
        )

    async def generate_narrative(
        self,
        data: NarrativeInput,
        *,
        hidden_truths: list[str] | None = None,
        npc_private_facts: list[str] | None = None,
    ) -> NarrativeWithReviewResult:
        try:
            result = await self.revision_loop.run(
                data,
                hidden_truths=hidden_truths,
                npc_private_facts=npc_private_facts,
            )
        except Exception as exc:
            logger.warning("RevisionLoop failed; using local fallback narrative: %s", exc)
            result = NarrativeWithReviewResult(
                narrative=mock_narrative(data),
                review=mock_critic_approve(),
                revision_count=0,
                used_fallback=True,
                tokens_used=0,
                latency_ms=0,
            )
        return NarrativeWithReviewResult(
            narrative=result.narrative,
            review=result.review,
            revision_count=result.revision_count,
            used_fallback=result.used_fallback,
            tokens_used=result.tokens_used,
            latency_ms=result.latency_ms,
        )

    async def generate_summary(self, data: SummaryInput) -> AgentResult[SummaryOutput]:
        try:
            output, llm = await self.summary_agent.generate(data)
        except Exception as exc:
            logger.warning("SummaryAgent failed; using local fallback summary: %s", exc)
            output = mock_summary(data)
            llm = None
        return AgentResult(
            output=output,
            tokens_used=llm.tokens_used if llm else 0,
            latency_ms=llm.latency_ms if llm else 0,
        )

    async def generate_guidance(self, data: GuidanceInput) -> AgentResult[GuidanceOutput]:
        try:
            output, llm = await self.guidance_agent.generate(data)
        except Exception as exc:
            logger.warning("GuidanceAgent failed; using local fallback guidance: %s", exc)
            output = mock_guidance(data)
            llm = None
        return AgentResult(
            output=output,
            tokens_used=llm.tokens_used if llm else 0,
            latency_ms=llm.latency_ms if llm else 0,
        )

    async def extract_rulebook(
        self, data: RulebookExtractionInput
    ) -> AgentResult[RulebookExtractionOutput]:
        try:
            output, llm = await self.rulebook_extractor_agent.extract(data)
        except Exception as exc:
            logger.warning("RulebookExtractorAgent failed; using local fallback: %s", exc)
            output = mock_rulebook_extract(data)
            llm = None
        return AgentResult(
            output=output,
            tokens_used=llm.tokens_used if llm else 0,
            latency_ms=llm.latency_ms if llm else 0,
        )

    async def extract_module(
        self, data: ModuleExtractionInput
    ) -> AgentResult[ModuleExtractionOutput]:
        try:
            output, llm = await self.module_extractor_agent.extract(data)
        except Exception as exc:
            logger.warning("ModuleExtractorAgent failed; using local fallback: %s", exc)
            output = mock_module_extract(data)
            llm = None
        return AgentResult(
            output=output,
            tokens_used=llm.tokens_used if llm else 0,
            latency_ms=llm.latency_ms if llm else 0,
        )

    @staticmethod
    def build_opening_input(
        world: str | WorldContext,
        character: CharacterCard | dict,
    ) -> OpeningInput:
        if isinstance(character, dict):
            character = CharacterCard.model_validate(character)
        return OpeningInput(world=world, character=character)


_ai_module: AIModule | None = None


def get_ai_module() -> AIModule:
    global _ai_module
    if _ai_module is None:
        _ai_module = AIModule()
    return _ai_module

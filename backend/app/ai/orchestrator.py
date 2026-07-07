from __future__ import annotations

from app.ai.schemas.action_parse import ActionParseInput, ActionParseOutput
from app.ai.schemas.agent_result import AgentResult
from app.ai.schemas.character import CharacterCard, WorldContext
from app.ai.schemas.narrative import NarrativeInput, NarrativeWithReviewResult
from app.ai.schemas.opening import OpeningInput, OpeningOutput
from app.ai.schemas.summary import SummaryInput, SummaryOutput
from app.ai.services.action_parser_agent import ActionParserAgent
from app.ai.services.opening_agent import OpeningAgent
from app.ai.services.revision_loop import RevisionLoop
from app.ai.services.summary_agent import SummaryAgent


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

    async def generate_opening(self, data: OpeningInput) -> AgentResult[OpeningOutput]:
        output, llm = await self.opening_agent.generate(data)
        return AgentResult(
            output=output,
            tokens_used=llm.tokens_used if llm else 0,
            latency_ms=llm.latency_ms if llm else 0,
        )

    async def parse_action(self, data: ActionParseInput) -> AgentResult[ActionParseOutput]:
        output, llm = await self.action_parser_agent.parse(data)
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
        result = await self.revision_loop.run(
            data,
            hidden_truths=hidden_truths,
            npc_private_facts=npc_private_facts,
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
        output, llm = await self.summary_agent.generate(data)
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

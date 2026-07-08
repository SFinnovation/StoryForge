"""AI 服务门面 — 封装 AIModule，供 session/action/report 调用。"""

from __future__ import annotations

from backend.app.ai import get_ai_module
from backend.app.ai.schemas import (
    ActionParseInput,
    ActionParseOutput,
    AgentResult,
    CharacterCard,
    CheckResult,
    NarrativeInput,
    NarrativeWithReviewResult,
    OpeningInput,
    OpeningOutput,
    SummaryInput,
    SummaryOutput,
)


class AIService:
    def __init__(self) -> None:
        self._module = get_ai_module()

    async def generate_opening(self, data: OpeningInput) -> AgentResult[OpeningOutput]:
        return await self._module.generate_opening(data)

    async def parse_action(self, data: ActionParseInput) -> AgentResult[ActionParseOutput]:
        return await self._module.parse_action(data)

    async def generate_narrative(
        self,
        data: NarrativeInput,
        *,
        hidden_truths: list[str] | None = None,
        npc_private_facts: list[str] | None = None,
    ) -> NarrativeWithReviewResult:
        return await self._module.generate_narrative(
            data,
            hidden_truths=hidden_truths,
            npc_private_facts=npc_private_facts,
        )

    async def generate_summary(self, data: SummaryInput) -> AgentResult[SummaryOutput]:
        return await self._module.generate_summary(data)


_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service

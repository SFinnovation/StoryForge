from __future__ import annotations

from dataclasses import dataclass

from backend.app.ai.schemas.critic import CriticOutput
from backend.app.ai.schemas.narrative import NarrativeInput, NarrativeOutput
from backend.app.ai.services.critic_agent import CriticAgent
from backend.app.ai.services.llm_client import LLMResponse
from backend.app.ai.services.narrative_agent import NarrativeAgent
from backend.app.ai.services.prompt_loader import load_prompt
from backend.app.core.config import settings


@dataclass
class RevisionLoopResult:
    narrative: NarrativeOutput
    review: CriticOutput
    revision_count: int
    used_fallback: bool
    tokens_used: int
    latency_ms: int


class RevisionLoop:
    """NarrativeAgent + CriticAgent 修正循环。"""

    def __init__(self) -> None:
        self.narrative_agent = NarrativeAgent()
        self.critic_agent = CriticAgent()

    async def run(
        self,
        data: NarrativeInput,
        *,
        hidden_truths: list[str] | None = None,
        npc_private_facts: list[str] | None = None,
    ) -> RevisionLoopResult:
        tokens_used = 0
        latency_ms = 0
        revision_count = 0
        current_input = data.model_copy()

        narrative, llm = await self.narrative_agent.generate(current_input)
        if llm:
            tokens_used += llm.tokens_used
            latency_ms += llm.latency_ms

        if not settings.AI_ENABLE_CRITIC:
            from backend.app.ai.services.fallbacks import mock_critic_approve

            review = mock_critic_approve()
            return RevisionLoopResult(
                narrative=narrative,
                review=review,
                revision_count=0,
                used_fallback=False,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
            )

        review, critic_llm = await self.critic_agent.review(
            narrative,
            current_input,
            hidden_truths=hidden_truths,
            npc_private_facts=npc_private_facts,
        )
        if critic_llm:
            tokens_used += critic_llm.tokens_used
            latency_ms += critic_llm.latency_ms

        while not review.approved and revision_count < settings.AI_MAX_REVISIONS:
            revision_count += 1
            current_input = current_input.model_copy(
                update={
                    "revision_instructions": review.revision_instructions,
                    "previous_narration": narrative.narration,
                }
            )
            narrative, llm = await self.narrative_agent.revise(current_input)
            if llm:
                tokens_used += llm.tokens_used
                latency_ms += llm.latency_ms
            review, critic_llm = await self.critic_agent.review(
                narrative,
                current_input,
                hidden_truths=hidden_truths,
                npc_private_facts=npc_private_facts,
            )
            if critic_llm:
                tokens_used += critic_llm.tokens_used
                latency_ms += critic_llm.latency_ms

        used_fallback = False
        if not review.approved and settings.AI_FALLBACK_ON_CRITIC_FAIL:
            used_fallback = True
            fallback_text = load_prompt("fallback_narration.txt").strip()
            narrative = narrative.model_copy(
                update={
                    "narration": fallback_text,
                    "visible_result": "系统采用保守叙事。",
                    "new_clues": [],
                    "next_options": ["重新调查", "与 NPC 对话", "尝试其他行动"],
                }
            )
            review = review.model_copy(
                update={
                    "approved": True,
                    "overall_score": max(review.overall_score, settings.AI_CRITIC_PASS_SCORE),
                    "fatal_errors": [],
                    "revision_instructions": [],
                }
            )

        return RevisionLoopResult(
            narrative=narrative,
            review=review,
            revision_count=revision_count,
            used_fallback=used_fallback,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

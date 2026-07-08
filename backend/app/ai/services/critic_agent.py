from __future__ import annotations

from backend.app.ai.schemas.critic import CriticOutput
from backend.app.ai.schemas.narrative import NarrativeInput, NarrativeOutput
from backend.app.ai.services.fallbacks import mock_critic_approve
from backend.app.ai.services.json_utils import dumps_context, parse_model
from backend.app.ai.services.llm_client import LLMResponse, get_llm_client
from backend.app.ai.services.prompt_loader import load_prompt, render_prompt
from backend.app.core.config import settings


class CriticAgent:
    """辅审核 Agent — 审查主叙事是否合理。"""

    async def review(
        self,
        narrative: NarrativeOutput,
        narrative_input: NarrativeInput,
        *,
        hidden_truths: list[str] | None = None,
        npc_private_facts: list[str] | None = None,
    ) -> tuple[CriticOutput, LLMResponse | None]:
        client = get_llm_client()
        if not client.enabled:
            return mock_critic_approve(), None

        template = load_prompt("critic_agent.txt")
        user_content = render_prompt(
            template,
            pass_score=str(settings.AI_CRITIC_PASS_SCORE),
            narrative_output=dumps_context(narrative),
            rule_result=dumps_context(narrative_input.check_result or {}),
            world_facts=dumps_context(narrative_input.public_world_facts),
            hidden_truths=dumps_context(hidden_truths or []),
            npc_private_facts=dumps_context(npc_private_facts or []),
            player_card=dumps_context(narrative_input.character or {}),
            previous_events=dumps_context(
                {
                    "recent_summary": narrative_input.recent_summary,
                    "known_clues": narrative_input.known_clues,
                    "current_scene": narrative_input.current_scene,
                }
            ),
        )
        system = "你是 StoryForge CriticAgent。只输出 JSON。"
        model = settings.AI_CRITIC_MODEL or None
        llm = await client.chat(system, user_content, model=model, temperature=0.2)
        output = parse_model(llm.content, CriticOutput)
        output = self._apply_thresholds(output)
        return output, llm

    def _apply_thresholds(self, review: CriticOutput) -> CriticOutput:
        scores = review.scores
        force_reject = (
            scores.rule_consistency < 70
            or scores.npc_knowledge_boundary < 70
            or bool(review.fatal_errors)
            or review.overall_score < settings.AI_CRITIC_PASS_SCORE
        )
        approved = review.approved and not force_reject
        if force_reject:
            approved = False
        return review.model_copy(update={"approved": approved})

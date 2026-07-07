"""玩家行动编排 — 对齐 implementation-spec §8.2 / §11.2。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.schemas import ActionParseInput, CheckResult, NarrativeInput
from app.models.game import AiReview, Character, CharacterAttributes, Fact, GameSession
from app.schemas.session_schema import (
    ActionData,
    ActionMetaDTO,
    AiReviewDTO,
    CheckDTO,
    MessageDTO,
    SessionMetaDTO,
    StoryDTO,
)
from app.services.ai_service import get_ai_service
from app.services.clue_pressure import calculate as calc_clue_pressure
from app.services.context_builder import build_for_action
from app.services.rule_service import roll_check
from app.services.session_service import get_playing_session
from app.services.state_committer import commit_action


async def handle_action(
    db: Session,
    session_id: int,
    user_id: int,
    action_text: str,
) -> ActionData:
    session = get_playing_session(db, session_id, user_id)
    character = db.get(Character, session.character_id)
    attrs = (
        db.query(CharacterAttributes)
        .filter(CharacterAttributes.character_id == character.id)
        .first()
        if character
        else None
    )

    ctx = build_for_action(db, session)
    ai = get_ai_service()

    parse_result = await ai.parse_action(
        ActionParseInput(
            player_action=action_text,
            current_scene=ctx.current_scene,
            character=ctx.character,
            recent_summary=ctx.recent_summary,
        )
    )
    parsed = parse_result.output
    tokens_used = parse_result.tokens_used
    latency_ms = parse_result.latency_ms

    check_outcome = None
    check_result_model: CheckResult | None = None

    if parsed.needs_check and character is not None:
        check_outcome = roll_check(
            character,
            attrs,
            check_type=parsed.check_type,
            skill_key=parsed.skill_key,
            attribute_used=parsed.attribute_used,
            dc=parsed.suggested_dc,
        )
        check_result_model = CheckResult(
            success=check_outcome.is_success,
            dice_roll=check_outcome.dice_roll,
            final_value=check_outcome.final_value,
            dc=check_outcome.dc,
            check_type=check_outcome.check_type,
            attribute_used=check_outcome.attribute_used,
            result_text=check_outcome.result_text,
        )

    story = await ai.generate_narrative(
        NarrativeInput(
            player_action=action_text,
            check_result=check_result_model,
            current_scene=ctx.current_scene,
            known_clues=ctx.known_clues,
            clue_pressure=ctx.clue_pressure,
            world=ctx.world,
            character=ctx.character,
            recent_summary=ctx.recent_summary,
            public_world_facts=ctx.public_world_facts,
            visible_npcs=ctx.visible_npcs,
        ),
        hidden_truths=ctx.hidden_truths,
        npc_private_facts=ctx.npc_private_facts,
    )
    tokens_used += story.tokens_used
    latency_ms += story.latency_ms

    commit = commit_action(
        db,
        session,
        action_text=action_text,
        check=check_outcome,
        narrative=story.narrative,
        review=story.review,
        revision_count=story.revision_count,
        used_fallback=story.used_fallback,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
    )
    meta = calc_clue_pressure(db, session)
    db.commit()

    check_dto: CheckDTO | None = None
    if commit.check_record is not None:
        c = commit.check_record
        check_dto = CheckDTO(
            id=c.id,
            check_type=c.check_type,
            skill_key=c.skill_key,
            attribute_used=c.attribute_used,
            dc=c.dc,
            dice_roll=c.dice_roll,
            ability_modifier=c.attribute_bonus,
            skill_bonus=c.skill_bonus,
            final_value=c.final_value,
            is_success=bool(c.is_success),
            result_text=c.result_text or "",
        )

    new_clues = [
        {"title": cl.title, "content": cl.content, "importance": cl.importance}
        for cl in commit.new_clue_records
    ]

    return ActionData(
        player_message=MessageDTO(
            id=commit.player_message.id,
            content=commit.player_message.content,
            message_type=commit.player_message.message_type,
            created_at=commit.player_message.created_at,
        ),
        check=check_dto,
        story=StoryDTO(
            message_id=commit.story_message.id,
            narration=story.narrative.narration,
            visible_result=story.narrative.visible_result,
            new_clues=new_clues,
            task_updates=[t.model_dump() for t in story.narrative.state_updates.task_updates],
            next_options=story.narrative.next_options,
        ),
        session_meta=SessionMetaDTO(
            current_scene=meta["current_scene"],
            clue_pressure=meta["clue_pressure"],
            turns_since_key_clue=meta["turns_since_key_clue"],
        ),
        ai_review=AiReviewDTO(
            approved=story.review.approved,
            overall_score=story.review.overall_score,
            revision_count=story.revision_count,
            used_fallback=story.used_fallback,
            scores=story.review.scores.model_dump(),
        ),
        meta=ActionMetaDTO(tokens_used=tokens_used, latency_ms=latency_ms),
    )


def get_session_meta(db: Session, session_id: int, user_id: int) -> SessionMetaDTO:
    session = db.get(GameSession, session_id)
    if session is None:
        raise StoryForgeError("session not found", status_code=404)
    if session.user_id != user_id:
        raise StoryForgeError("forbidden", status_code=403)
    meta = calc_clue_pressure(db, session)
    db.commit()
    return SessionMetaDTO(
        current_scene=meta["current_scene"],
        clue_pressure=meta["clue_pressure"],
        turns_since_key_clue=meta["turns_since_key_clue"],
    )


def list_facts(db: Session, session_id: int, user_id: int, scope: str = "player_known") -> list[dict]:
    session = db.get(GameSession, session_id)
    if session is None or session.user_id != user_id:
        return []
    rows = (
        db.query(Fact)
        .filter(Fact.session_id == session_id, Fact.fact_type == scope)
        .all()
    )
    return [
        {
            "fact_id": f"fact_{f.id}",
            "content": f.content,
            "fact_type": f.fact_type,
            "related_scene": f.related_scene,
            "importance": f.importance,
            "status": f.status,
        }
        for f in rows
    ]


def list_ai_reviews(db: Session, session_id: int, user_id: int, limit: int = 10) -> list[dict]:
    session = db.get(GameSession, session_id)
    if session is None or session.user_id != user_id:
        return []
    rows = (
        db.query(AiReview)
        .filter(AiReview.session_id == session_id)
        .order_by(AiReview.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "message_id": r.message_id,
            "approved": bool(r.approved),
            "overall_score": r.overall_score,
            "scores": {
                "rule_consistency": r.rule_score,
                "world_consistency": r.world_score,
                "context_continuity": r.context_score,
                "character_alignment": r.character_score,
                "npc_knowledge_boundary": r.npc_boundary_score,
                "clue_progression": r.clue_score,
            },
            "revision_count": r.revision_count,
            "created_at": r.created_at,
        }
        for r in rows
    ]

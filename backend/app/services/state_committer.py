"""State Committer — 校验 AI 输出后落库。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.schemas.critic import CriticOutput
from app.ai.schemas.narrative import NarrativeOutput
from app.models.game import ActionCheck, AiReview, Clue, GameSession, Message, Task
from app.services.fact_repository import commit_new_facts, update_npc_alertness
from app.services.rule_service import CheckOutcome


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class CommitActionResult:
    player_message: Message
    dice_message: Message | None
    story_message: Message
    check_record: ActionCheck | None
    new_clue_records: list[Clue]


def commit_opening(
    db: Session,
    session: GameSession,
    *,
    narration: str,
    scene_title: str,
    main_task: str,
    tokens_used: int = 0,
    latency_ms: int = 0,
) -> Message:
    session.current_scene = scene_title
    session.current_task = main_task
    session.summary = narration[:200]

    msg = Message(
        session_id=session.id,
        sender_type="ai",
        sender_name="主持人",
        content=narration,
        message_type="narration",
        tokens_used=tokens_used or None,
        latency_ms=latency_ms or None,
        created_at=_now(),
    )
    db.add(msg)

    task = Task(
        session_id=session.id,
        title=main_task,
        description=main_task,
        status="doing",
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(task)
    db.flush()
    return msg


def commit_action(
    db: Session,
    session: GameSession,
    *,
    action_text: str,
    check: CheckOutcome | None,
    narrative: NarrativeOutput,
    review: CriticOutput,
    revision_count: int,
    used_fallback: bool,
    tokens_used: int,
    latency_ms: int,
) -> CommitActionResult:
    player_msg = Message(
        session_id=session.id,
        sender_type="player",
        sender_name="玩家",
        content=action_text,
        message_type="action",
        created_at=_now(),
    )
    db.add(player_msg)
    db.flush()

    check_record: ActionCheck | None = None
    dice_msg: Message | None = None

    if check is not None:
        dice_content = check.result_text
        dice_msg = Message(
            session_id=session.id,
            sender_type="system",
            sender_name="系统",
            content=dice_content,
            message_type="dice",
            created_at=_now(),
        )
        db.add(dice_msg)
        db.flush()

        check_record = ActionCheck(
            session_id=session.id,
            message_id=dice_msg.id,
            action_text=action_text,
            check_type=check.check_type,
            skill_key=check.skill_key,
            attribute_used=check.attribute_used,
            dc=check.dc,
            dice_roll=check.dice_roll,
            attribute_bonus=check.ability_modifier,
            skill_bonus=check.skill_bonus,
            final_value=check.final_value,
            is_success=1 if check.is_success else 0,
            result_text=check.result_text,
            created_at=_now(),
        )
        db.add(check_record)
        db.flush()

    story_msg = Message(
        session_id=session.id,
        sender_type="ai",
        sender_name="主持人",
        content=narrative.narration,
        message_type="narration",
        tokens_used=tokens_used or None,
        latency_ms=latency_ms or None,
        created_at=_now(),
    )
    db.add(story_msg)
    db.flush()

    new_clues: list[Clue] = []
    for clue in narrative.new_clues:
        if not clue.title:
            continue
        existing = (
            db.query(Clue)
            .filter(Clue.session_id == session.id, Clue.title == clue.title)
            .first()
        )
        if existing:
            continue
        record = Clue(
            session_id=session.id,
            title=clue.title,
            content=clue.content,
            source_scene=session.current_scene,
            importance=clue.importance,
            discovered_at=_now(),
        )
        db.add(record)
        new_clues.append(record)

    for task_upd in narrative.state_updates.task_updates:
        task = (
            db.query(Task)
            .filter(Task.session_id == session.id, Task.title == task_upd.title)
            .first()
        )
        if task:
            task.status = task_upd.status
            task.updated_at = _now()
        else:
            db.add(
                Task(
                    session_id=session.id,
                    title=task_upd.title,
                    status=task_upd.status,
                    created_at=_now(),
                    updated_at=_now(),
                )
            )

    if narrative.state_updates.scene:
        session.current_scene = narrative.state_updates.scene
    if narrative.state_updates.summary_delta:
        session.summary = (session.summary or "") + narrative.state_updates.summary_delta

    commit_new_facts(
        db,
        session.id,
        narrative.state_updates.new_facts,
        current_scene=session.current_scene,
    )
    update_npc_alertness(db, session.id, narrative.state_updates.npc_alertness)

    scores = review.scores
    ai_review = AiReview(
        session_id=session.id,
        message_id=story_msg.id,
        overall_score=review.overall_score,
        rule_score=scores.rule_consistency,
        world_score=scores.world_consistency,
        context_score=scores.context_continuity,
        character_score=scores.character_alignment,
        npc_boundary_score=scores.npc_knowledge_boundary,
        clue_score=scores.clue_progression,
        approved=1 if review.approved else 0,
        revision_count=revision_count,
        used_fallback=1 if used_fallback else 0,
        fatal_errors_json=json.dumps(review.fatal_errors, ensure_ascii=False),
        revision_instructions_json=json.dumps(review.revision_instructions, ensure_ascii=False),
        created_at=_now(),
    )
    db.add(ai_review)
    db.flush()

    return CommitActionResult(
        player_message=player_msg,
        dice_message=dice_msg,
        story_message=story_msg,
        check_record=check_record,
        new_clue_records=new_clues,
    )

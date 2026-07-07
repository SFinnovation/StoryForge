"""会话上下文构建 — 为 AI Agent 裁剪可见信息。"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.ai.schemas.character import CharacterCard, WorldContext
from app.ai.schemas.opening import OpeningInput
from app.models.game import Character, Clue, Fact, GameSession, Message, World
from app.services.memory_retriever import (
    get_hidden_truths,
    get_npc_private_facts,
    list_npc_profiles,
)


@dataclass
class ActionContext:
    world: WorldContext
    character: CharacterCard
    current_scene: str
    known_clues: list[str] = field(default_factory=list)
    clue_pressure: float = 0.0
    recent_summary: str = ""
    public_world_facts: list[str] = field(default_factory=list)
    hidden_truths: list[str] = field(default_factory=list)
    npc_private_facts: list[str] = field(default_factory=list)
    visible_npcs: list[dict] = field(default_factory=list)


def character_to_card(character: Character) -> CharacterCard:
    return CharacterCard(
        name=character.name,
        profession=character.profession,
        background=character.background or "",
        motivation=character.motivation or "",
    )


def build_for_opening(db: Session, world: World, character: Character) -> OpeningInput:
    return OpeningInput(
        world=WorldContext(
            name=world.name,
            description=world.description,
            opening_prompt=world.opening_prompt,
        ),
        character=character_to_card(character),
    )


def build_for_action(db: Session, session: GameSession) -> ActionContext:
    world = db.get(World, session.world_id)
    character = db.get(Character, session.character_id)
    if world is None or character is None:
        raise ValueError("session world or character missing")

    clues = (
        db.query(Clue)
        .filter(Clue.session_id == session.id)
        .order_by(Clue.discovered_at.desc())
        .limit(20)
        .all()
    )
    known_clues = [c.title for c in clues]

    facts_player = (
        db.query(Fact)
        .filter(Fact.session_id == session.id, Fact.fact_type == "player_known")
        .all()
    )
    facts_public = (
        db.query(Fact)
        .filter(Fact.session_id == session.id, Fact.fact_type == "world_public")
        .all()
    )
    player_facts = [f.content for f in facts_player]
    public_facts = [f.content for f in facts_public]

    hidden = get_hidden_truths(db, session.id)
    npc_private = get_npc_private_facts(db, session.id)
    visible_npcs = list_npc_profiles(db, session.id)

    recent_msgs = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.id.desc())
        .limit(10)
        .all()
    )
    recent_summary = session.summary or ""
    if not recent_summary and recent_msgs:
        recent_summary = " | ".join(m.content[:80] for m in reversed(recent_msgs))

    return ActionContext(
        world=WorldContext(
            name=world.name,
            description=world.description,
            opening_prompt=world.opening_prompt,
        ),
        character=character_to_card(character),
        current_scene=session.current_scene or world.name,
        known_clues=known_clues,
        clue_pressure=float(session.clue_pressure or 0.0),
        recent_summary=recent_summary,
        public_world_facts=public_facts + player_facts,
        hidden_truths=hidden,
        npc_private_facts=npc_private,
        visible_npcs=visible_npcs,
    )


def build_for_summary(db: Session, session: GameSession) -> SummaryInput:
    from app.ai.schemas import CheckResult, SummaryInput

    character = db.get(Character, session.character_id)
    world = db.get(World, session.world_id)
    if character is None or world is None:
        raise ValueError("session world or character missing")

    player_actions = [
        m.content
        for m in db.query(Message)
        .filter(Message.session_id == session.id, Message.message_type == "action")
        .order_by(Message.id)
        .all()
    ]
    from app.models.game import ActionCheck

    checks = db.query(ActionCheck).filter(ActionCheck.session_id == session.id).all()
    check_results = [
        CheckResult(
            success=bool(c.is_success),
            dice_roll=c.dice_roll,
            final_value=c.final_value,
            dc=c.dc,
            check_type=c.check_type,
            attribute_used=c.attribute_used,
            result_text=c.result_text,
        )
        for c in checks
    ]
    narrations = [
        m.content
        for m in db.query(Message)
        .filter(Message.session_id == session.id, Message.message_type == "narration")
        .order_by(Message.id)
        .all()
    ]
    discovered = [
        c.title
        for c in db.query(Clue).filter(Clue.session_id == session.id).all()
    ]

    return SummaryInput(
        world=world.name,
        character=character_to_card(character),
        player_actions=player_actions,
        check_results=check_results,
        ai_narrations=narrations,
        discovered_clues=discovered,
        session_summary=session.summary or "",
    )

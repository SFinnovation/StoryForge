# -*- coding: utf-8 -*-
"""多人房间上下文构建 — GuidanceAgent 等低泄露场景 (§6.5)

仅注入 player_known / world_public 类事实与可见线索，绝不包含
hidden_truth / npc_private。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.ai.schemas.character import CharacterCard, WorldContext
from backend.app.ai.schemas.guidance import GuidanceInput
from backend.app.models.models import Character, Clue, GameSession, Room, RoomMember, Task, World
from backend.app.services.content_ingestion_service import load_world_content_context
from backend.app.services.context_builder import character_to_card
from backend.app.services.memory_retriever import MemoryRetriever


def build_for_guidance(
    db: Session,
    room: Room,
    member: RoomMember,
    session: GameSession | None,
    character: Character | None,
) -> GuidanceInput:
    world = db.get(World, room.world_id)
    pack_ctx = load_world_content_context(db, world) if world else {}

    if character is None and member.character_id:
        character = db.get(Character, member.character_id)

    world_ctx_name = world.name if world else "未知世界"
    world_desc = world.description if world else ""
    world_style = pack_ctx.get("rulebook").world_style if pack_ctx.get("rulebook") else (
        world.type if world else ""
    )

    char_card = (
        character_to_card(character)
        if character
        else CharacterCard(
            name=member.display_name or "冒险者",
            profession="",
            background="",
            motivation="",
        )
    )

    world_ctx = WorldContext(
        name=world_ctx_name,
        description=world_desc or "",
        style=world_style or "",
        opening_prompt=(world.opening_prompt or "") if world else "",
    )

    if session is None:
        return GuidanceInput(
            question="",
            world=world_ctx,
            character=char_card,
            current_scene="等待房主开始游戏",
            public_world_facts=pack_ctx.get("public_world_facts", [])[:12],
            recent_summary=pack_ctx.get("story_summary", "")[:300],
        )

    memory = MemoryRetriever(db)
    clues = (
        db.query(Clue)
        .filter(Clue.session_id == session.id)
        .order_by(Clue.discovered_at.desc())
        .limit(15)
        .all()
    )
    known_clues = [c.title for c in clues]
    known_clues.extend(pack_ctx.get("player_known_clues", [])[:8])

    public_facts = [f.content for f in memory.get_world_public_facts(session.id)]
    public_facts.extend(
        f.content for f in memory.get_player_known_facts(session.id)
    )
    public_facts.extend(pack_ctx.get("public_world_facts", [])[:12])
    # 去重保序
    seen: set[str] = set()
    public_facts = [x for x in public_facts if x and not (x in seen or seen.add(x))]

    visible_npcs = memory.get_visible_npcs(session.id, session.current_scene)
    if not visible_npcs:
        visible_npcs = [
            {
                "npc_id": n.get("npc_id"),
                "name": n.get("name"),
                "personality": n.get("personality") or n.get("description"),
            }
            for n in pack_ctx.get("visible_npcs", [])
            if isinstance(n, dict)
        ]

    active_tasks = [
        t.title
        for t in db.query(Task)
        .filter(Task.session_id == session.id, Task.status.in_(("todo", "doing")))
        .all()
    ]

    return GuidanceInput(
        question="",
        world=world_ctx,
        character=char_card,
        current_scene=session.current_scene or pack_ctx.get("current_scene") or world_ctx_name,
        current_task=session.current_task,
        known_clues=known_clues[:15],
        public_world_facts=public_facts[:20],
        visible_npcs=visible_npcs[:8],
        active_tasks=active_tasks[:6],
        recent_summary=(session.summary or pack_ctx.get("story_summary") or "")[:400],
    )

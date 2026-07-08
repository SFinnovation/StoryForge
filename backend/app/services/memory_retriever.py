# -*- coding: utf-8 -*-
"""Memory Retriever (ai-module-design §11.1)

按 Agent 身份提供不同可见性的记忆读取 (§4.1 可见性矩阵):
  主 Agent  -> world_public + player_known (+ session_fact/temporary)
  辅 Agent  -> 额外拿到完整 hidden_truth + npc_private (§1.2 硬约束 3)
  前端     -> get_player_known_facts (GET /sessions/{id}/facts?scope=player_known)
"""
import json

from sqlalchemy.orm import Session

from backend.app.models.models import Fact, NpcProfile
from backend.app.repositories import FactRepo, NpcRepo

MAIN_AGENT_TYPES = ["world_public", "player_known", "session_fact", "temporary"]
CRITIC_ONLY_TYPES = ["hidden_truth", "npc_private"]


class MemoryRetriever:
    def __init__(self, db: Session):
        self.facts = FactRepo(db)
        self.npcs = NpcRepo(db)

    # ---------- Fact ----------

    def get_player_known_facts(self, session_id: int) -> list[Fact]:
        """主 Agent / 前端可见集合 (经玩家可见性裁剪)"""
        return self.facts.list_by_session(
            session_id, fact_types=MAIN_AGENT_TYPES, visibility="player")

    def get_world_public_facts(self, session_id: int) -> list[Fact]:
        return self.facts.list_by_session(session_id, fact_types=["world_public"])

    def get_hidden_truths(self, session_id: int) -> list[Fact]:
        """仅辅 Agent (Critic) 可调用; 含 locked 未解锁项"""
        return self.facts.list_by_session(session_id, fact_types=["hidden_truth"])

    def get_npc_private_facts(self, session_id: int) -> list[Fact]:
        """仅辅 Agent (Critic) 可调用"""
        return self.facts.list_by_session(session_id, fact_types=["npc_private"])

    # ---------- NPC ----------

    def get_visible_npcs(self, session_id: int, scene: str | None) -> list[dict]:
        """主 Agent 视角: 只给人格/说话风格/知识范围, 不给 forbidden_knowledge"""
        return [
            {
                "npc_id": n.npc_id,
                "name": n.name,
                "personality": n.personality,
                "speaking_style": n.speaking_style,
                "knowledge_scope": json.loads(n.knowledge_scope_json or "[]"),
                "alertness": n.alertness,
            }
            for n in self.npcs.list_visible(session_id, scene)
        ]

    def get_npc_boundaries(self, session_id: int) -> list[dict]:
        """辅 Agent 视角: 含 forbidden_knowledge, 用于 npc_knowledge_boundary 审核"""
        return [
            {
                "npc_id": n.npc_id,
                "name": n.name,
                "knowledge_scope": json.loads(n.knowledge_scope_json or "[]"),
                "forbidden_knowledge": json.loads(n.forbidden_knowledge_json or "[]"),
            }
            for n in self.npcs.list_by_session(session_id)
        ]


def get_facts_by_types(db: Session, session_id: int, fact_types: list[str]) -> list[Fact]:
    return FactRepo(db).list_by_session(session_id, fact_types=fact_types)


def get_player_known_facts(db: Session, session_id: int) -> list[str]:
    return [f.content for f in MemoryRetriever(db).get_player_known_facts(session_id)]


def get_hidden_truths(db: Session, session_id: int) -> list[str]:
    return [f.content for f in MemoryRetriever(db).get_hidden_truths(session_id)]


def get_npc_private_facts(db: Session, session_id: int) -> list[str]:
    return [f.content for f in MemoryRetriever(db).get_npc_private_facts(session_id)]


def list_npc_profiles(db: Session, session_id: int) -> list[dict]:
    rows = NpcRepo(db).list_by_session(session_id)
    return [
        {
            "npc_id": npc.npc_id,
            "name": npc.name,
            "personality": npc.personality or "",
            "knowledge_scope": json.loads(npc.knowledge_scope_json or "[]"),
            "forbidden_knowledge": json.loads(npc.forbidden_knowledge_json or "[]"),
            "speaking_style": npc.speaking_style or "",
            "alertness": npc.alertness,
            "current_scene": npc.related_scene,
        }
        for npc in rows
    ]

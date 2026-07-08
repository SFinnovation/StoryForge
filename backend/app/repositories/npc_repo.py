# -*- coding: utf-8 -*-
"""NpcRepo (ai-module-design §11.1 / §4.3)

- list_visible: context_builder 组装 visible_npcs
  (related_scene 匹配当前场景, 或为 NULL 表示全场景可见)
- list_by_session: critic 上下文需要全部 NPC 的 forbidden_knowledge
- create_batch: world_seed 开局灌入模组 NPC
"""
import json

from backend.app.models.models import NpcProfile
from backend.app.repositories.base import BaseRepo


class NpcRepo(BaseRepo):

    def list_visible(self, session_id: int, scene: str | None = None) -> list[NpcProfile]:
        q = self.db.query(NpcProfile).filter_by(session_id=session_id, is_visible=1)
        if scene:
            q = q.filter(
                (NpcProfile.related_scene == scene) | (NpcProfile.related_scene.is_(None))
            )
        return q.order_by(NpcProfile.id.asc()).all()

    def list_by_session(self, session_id: int) -> list[NpcProfile]:
        return (
            self.db.query(NpcProfile)
            .filter_by(session_id=session_id)
            .order_by(NpcProfile.id.asc())
            .all()
        )

    def get_by_npc_id(self, session_id: int, npc_id: str) -> NpcProfile | None:
        return (
            self.db.query(NpcProfile)
            .filter_by(session_id=session_id, npc_id=npc_id)
            .first()
        )

    def create_batch(self, session_id: int, npcs: list[dict]) -> list[NpcProfile]:
        """world_seed 用: 批量写入模组 NPC, 依据 (session_id, npc_id) 幂等去重。

        npcs 元素: {"npc_id", "name", "personality", "knowledge_scope": [...],
                    "forbidden_knowledge": [...], "speaking_style", "related_scene"}
        """
        created: list[NpcProfile] = []
        for n in npcs:
            npc_id = (n.get("npc_id") or "").strip()
            if not npc_id or self.get_by_npc_id(session_id, npc_id):
                continue
            profile = NpcProfile(
                session_id=session_id, npc_id=npc_id, name=n["name"],
                personality=n.get("personality"),
                knowledge_scope_json=json.dumps(n.get("knowledge_scope", []), ensure_ascii=False),
                forbidden_knowledge_json=json.dumps(n.get("forbidden_knowledge", []), ensure_ascii=False),
                speaking_style=n.get("speaking_style"),
                related_scene=n.get("related_scene"),
            )
            self.db.add(profile)
            created.append(profile)
        if created:
            self.db.flush()
        return created

    def set_visibility(self, session_id: int, npc_id: str, visible: bool) -> NpcProfile:
        """NPC 登场/退场 (state_updates 可能调整)"""
        profile = self.get_by_npc_id(session_id, npc_id)
        if profile is None:
            raise ValueError(f"npc {npc_id} 不存在于 session {session_id}")
        profile.is_visible = 1 if visible else 0
        self.db.flush()
        return profile

    def adjust_alertness(self, session_id: int, npc_id: str, delta: int) -> NpcProfile:
        """state_updates.npc_alertness 应用; delta 合法性(|delta|<=3)由 state_committer 校验"""
        profile = self.get_by_npc_id(session_id, npc_id)
        if profile is None:
            raise ValueError(f"npc {npc_id} 不存在于 session {session_id}")
        profile.alertness = max(0, profile.alertness + delta)
        self.db.flush()
        return profile

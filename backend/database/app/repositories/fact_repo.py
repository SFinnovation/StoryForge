# -*- coding: utf-8 -*-
"""FactRepo (ai-module-design §11.1 / §4)

- list_by_session: memory_retriever 按类型+可见性取 Fact
  * 主 Agent:  fact_types=['world_public','player_known']
  * 辅 Agent:  fact_types=['hidden_truth','npc_private'] (完整可见, §1.2 硬约束 3)
- create:  state_committer 写入顺序第 6 步 (state_updates.new_facts)
- unlock:  hidden_truth 解锁: locked -> active
  (注意: 解锁 != 变为 player_known; §8.1 禁止 hidden_truth 直升 player_known,
   该校验在 state_committer 层执行, 本 Repo 的 create 也做兜底拦截)
"""
import json

from ..db.models import Fact
from .base import BaseRepo

VALID_FACT_TYPES = (
    "world_public", "player_known", "hidden_truth",
    "npc_private", "session_fact", "temporary",
)
PROTECTED_TYPES = ("hidden_truth", "npc_private")  # 不允许由 AI new_facts 随意创建/改写为玩家可见


class FactRepo(BaseRepo):

    def list_by_session(
        self,
        session_id: int,
        fact_types: list[str] | None = None,
        visibility: str | None = None,   # 'player' -> 仅玩家可见
        status: str | None = None,       # 'locked'/'active'/'resolved'
    ) -> list[Fact]:
        q = self.db.query(Fact).filter_by(session_id=session_id)
        if fact_types:
            q = q.filter(Fact.fact_type.in_(fact_types))
        if status:
            q = q.filter_by(status=status)
        rows = q.order_by(Fact.id.asc()).all()
        if visibility == "player":
            rows = [f for f in rows if self._player_visible(f)]
        return rows

    @staticmethod
    def _player_visible(fact: Fact) -> bool:
        """world_public / player_known 天然可见; 其余看 visibility_json.player"""
        if fact.fact_type in ("world_public", "player_known"):
            return True
        try:
            return bool(json.loads(fact.visibility_json).get("player", False))
        except (ValueError, TypeError):
            return False

    def get(self, fact_id: int) -> Fact | None:
        return self.db.get(Fact, fact_id)

    def create(
        self,
        session_id: int,
        content: str,
        fact_type: str,
        *,
        visibility: dict | None = None,
        related_scene: str | None = None,
        importance: str = "normal",
        status: str = "active",
        allow_protected: bool = False,
    ) -> Fact:
        """写入单条 Fact。

        allow_protected=False 时拒绝创建 hidden_truth / npc_private ——
        AI 的 new_facts 不得自行制造隐藏真相 (只有开局 world_seed 用
        allow_protected=True 灌入模组数据)。
        """
        if fact_type not in VALID_FACT_TYPES:
            raise ValueError(f"非法 fact_type: {fact_type}")
        if fact_type in PROTECTED_TYPES and not allow_protected:
            raise PermissionError(
                f"禁止通过常规通道创建 {fact_type} (仅 world_seed 允许)")
        vis = visibility if visibility is not None else {"player": False, "npcs": [], "dm": True}
        fact = Fact(
            session_id=session_id, content=content, fact_type=fact_type,
            visibility_json=json.dumps(vis, ensure_ascii=False),
            related_scene=related_scene, importance=importance, status=status,
        )
        self.db.add(fact)
        self.db.flush()
        return fact

    def unlock(self, fact_id: int) -> Fact:
        """locked -> active (剧情触发解锁; 类型保持不变)"""
        fact = self.db.get(Fact, fact_id)
        if fact is None:
            raise ValueError(f"fact {fact_id} 不存在")
        if fact.status == "locked":
            fact.status = "active"
            self.db.flush()
        return fact

    def resolve(self, fact_id: int) -> Fact:
        """active -> resolved (事实已了结)"""
        fact = self.db.get(Fact, fact_id)
        if fact is None:
            raise ValueError(f"fact {fact_id} 不存在")
        fact.status = "resolved"
        self.db.flush()
        return fact

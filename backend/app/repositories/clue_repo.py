# -*- coding: utf-8 -*-
"""ClueRepo (ai-module-design §11.1)

- list_by_session: context_builder 取玩家已知线索
- create_batch:    state_committer 写入顺序第 5 步;
                   按 title 去重 (§8.1 校验规则: 不重复 title)
"""
from backend.app.models.models import Clue
from backend.app.repositories.base import BaseRepo

VALID_IMPORTANCE = ("normal", "important", "key")


class ClueRepo(BaseRepo):

    def list_by_session(self, session_id: int) -> list[Clue]:
        return (
            self.db.query(Clue)
            .filter_by(session_id=session_id)
            .order_by(Clue.discovered_at.asc(), Clue.id.asc())
            .all()
        )

    def exists_title(self, session_id: int, title: str) -> bool:
        return (
            self.db.query(Clue.id)
            .filter_by(session_id=session_id, title=title)
            .first()
            is not None
        )

    def create_batch(self, session_id: int, clues: list[dict]) -> list[Clue]:
        """批量写入新线索, 自动跳过重复 title。

        clues 元素: {"title": str, "content": str, "importance": "normal|important|key",
                     "source_scene": str|None}
        返回实际写入的 Clue 列表 (跳过项不在其中)。
        """
        created: list[Clue] = []
        seen_in_batch: set[str] = set()
        for c in clues:
            title = (c.get("title") or "").strip()
            if not title:
                continue
            if title in seen_in_batch or self.exists_title(session_id, title):
                continue  # §8.1: 线索 title 不重复
            importance = c.get("importance", "normal")
            if importance not in VALID_IMPORTANCE:
                importance = "normal"
            clue = Clue(
                session_id=session_id, title=title,
                content=c.get("content"), source_scene=c.get("source_scene"),
                importance=importance,
            )
            self.db.add(clue)
            created.append(clue)
            seen_in_batch.add(title)
        if created:
            self.db.flush()
        return created

# -*- coding: utf-8 -*-
"""SessionRepo (ai-module-design §11.1)

- get_playing:  orchestrator 取"进行中"会话 (含归属校验)
- update_meta:  state_committer 写入顺序第 8 步 —— 场景/摘要/clue_pressure 回写
- finish:       结束会话 (session_service / report 流程用)
"""
from datetime import datetime

from backend.app.models.models import GameSession
from backend.app.repositories.base import BaseRepo


class SessionRepo(BaseRepo):

    def get(self, session_id: int) -> GameSession | None:
        return self.db.get(GameSession, session_id)

    def get_playing(self, session_id: int, user_id: int) -> GameSession | None:
        """取指定用户的进行中会话; 不存在/不属于该用户/已结束 均返回 None"""
        return (
            self.db.query(GameSession)
            .filter_by(id=session_id, user_id=user_id, status="playing")
            .first()
        )

    def update_meta(
        self,
        session_id: int,
        *,
        scene: str | None = None,
        summary_delta: str | None = None,
        clue_pressure: float | None = None,
        turns_since_key_clue: int | None = None,
        current_task: str | None = None,
    ) -> GameSession:
        """回写会话元数据; 仅更新传入的字段。

        summary_delta 追加到 summary 末尾(narrative 输出的 state_updates.summary_delta),
        clue_pressure 在写入前钳制到 [0.0, 1.0]。
        """
        session = self.db.get(GameSession, session_id)
        if session is None:
            raise ValueError(f"session {session_id} 不存在")
        if scene is not None:
            session.current_scene = scene
        if summary_delta:
            session.summary = f"{session.summary} {summary_delta}".strip() if session.summary else summary_delta
        if clue_pressure is not None:
            session.clue_pressure = min(1.0, max(0.0, clue_pressure))
        if turns_since_key_clue is not None:
            session.turns_since_key_clue = max(0, turns_since_key_clue)
        if current_task is not None:
            session.current_task = current_task
        self.db.flush()
        return session

    def finish(self, session_id: int, status: str = "finished") -> GameSession:
        """结束会话: playing -> finished/archived, 记录 ended_at"""
        if status not in ("finished", "archived"):
            raise ValueError(f"非法结束状态: {status}")
        session = self.db.get(GameSession, session_id)
        if session is None:
            raise ValueError(f"session {session_id} 不存在")
        session.status = status
        session.ended_at = datetime.utcnow()
        self.db.flush()
        return session

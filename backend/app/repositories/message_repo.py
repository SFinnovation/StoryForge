# -*- coding: utf-8 -*-
"""MessageRepo (ai-module-design §11.1)

- list_recent: context_builder 取最近 N 条消息 (AI_CONTEXT_MESSAGE_LIMIT, 默认 20)
- create:      state_committer 写入顺序第 1/3/4 步 (玩家行动 / 骰子 / AI 旁白)
- list_all:    summary_agent 聚合全局日志
"""
from backend.app.models.models import Message
from backend.app.repositories.base import BaseRepo

VALID_SENDER = ("player", "ai", "npc", "system")
VALID_TYPE = ("narration", "action", "dialogue", "dice", "clue", "task")


class MessageRepo(BaseRepo):

    def list_recent(self, session_id: int, limit: int = 20) -> list[Message]:
        """按时间倒序取最近 limit 条, 再翻回正序方便拼上下文"""
        rows = (
            self.db.query(Message)
            .filter_by(session_id=session_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(rows))

    def list_all(self, session_id: int) -> list[Message]:
        return (
            self.db.query(Message)
            .filter_by(session_id=session_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .all()
        )

    def create(
        self,
        session_id: int,
        sender_type: str,
        content: str,
        message_type: str,
        *,
        sender_name: str | None = None,
        tokens_used: int | None = None,
        latency_ms: int | None = None,
    ) -> Message:
        if sender_type not in VALID_SENDER:
            raise ValueError(f"非法 sender_type: {sender_type}")
        if message_type not in VALID_TYPE:
            raise ValueError(f"非法 message_type: {message_type}")
        msg = Message(
            session_id=session_id, sender_type=sender_type, sender_name=sender_name,
            content=content, message_type=message_type,
            tokens_used=tokens_used, latency_ms=latency_ms,
        )
        self.db.add(msg)
        self.db.flush()  # 立即拿到 msg.id, 供 action_checks.message_id / ai_reviews.message_id 关联
        return msg

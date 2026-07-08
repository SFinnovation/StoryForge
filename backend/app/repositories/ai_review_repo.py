# -*- coding: utf-8 -*-
"""AiReviewRepo (ai-module-design §11.1)

- create:      state_committer 写入顺序第 9 步 (Critic 六维评分落库)
- list_recent: GET /sessions/{id}/ai-reviews (P1 答辩展示)
"""
import json

from backend.app.models.models import AiReview
from backend.app.repositories.base import BaseRepo


class AiReviewRepo(BaseRepo):

    def create(
        self,
        session_id: int,
        *,
        approved: bool,
        overall_score: int,
        scores: dict | None = None,
        fatal_errors: list[str] | None = None,
        revision_instructions: list[str] | None = None,
        revision_count: int = 0,
        used_fallback: bool = False,
        message_id: int | None = None,
        tokens_used: int | None = None,
        latency_ms: int | None = None,
    ) -> AiReview:
        if not 0 <= overall_score <= 100:
            raise ValueError(f"overall_score 越界: {overall_score}")
        review = AiReview(
            session_id=session_id, message_id=message_id,
            approved=int(approved), overall_score=overall_score,
            scores_json=json.dumps(scores or {}, ensure_ascii=False),
            fatal_errors_json=json.dumps(fatal_errors or [], ensure_ascii=False),
            revision_instructions_json=json.dumps(revision_instructions or [], ensure_ascii=False),
            revision_count=revision_count, used_fallback=int(used_fallback),
            tokens_used=tokens_used, latency_ms=latency_ms,
        )
        self.db.add(review)
        self.db.flush()
        return review

    def list_recent(self, session_id: int, limit: int = 10) -> list[AiReview]:
        return (
            self.db.query(AiReview)
            .filter_by(session_id=session_id)
            .order_by(AiReview.created_at.desc(), AiReview.id.desc())
            .limit(limit)
            .all()
        )

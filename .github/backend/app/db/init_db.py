# -*- coding: utf-8 -*-
"""初始化建表 — 基于 ORM 元数据创建全部 12 张表与索引

用法:
    python -m app.db.init_db          # 建表(已存在则跳过)
    python -m app.db.init_db --drop   # 危险: 先删后建, 仅限开发环境
"""
import sys

from sqlalchemy import Index

from .database import Base, engine
from . import models  # noqa: F401  确保所有模型注册到 Base.metadata

# 索引定义(与 schema.sql 保持一致)
INDEXES = [
    Index("idx_sessions_user_status", models.GameSession.user_id, models.GameSession.status),
    Index("idx_messages_session", models.Message.session_id, models.Message.created_at),
    Index("idx_action_checks_session", models.ActionCheck.session_id),
    Index("idx_clues_session", models.Clue.session_id),
    Index("idx_tasks_session_status", models.Task.session_id, models.Task.status),
    Index("idx_characters_user", models.Character.user_id),
    # ---- AI 模块扩展表 (ai-module-design §11) ----
    # memory_retriever 按会话+类型取 Fact; context_builder 按场景取可见 NPC
    Index("idx_facts_session_type", models.Fact.session_id, models.Fact.fact_type),
    Index("idx_npc_profiles_session_scene", models.NpcProfile.session_id, models.NpcProfile.related_scene),
    Index("idx_ai_reviews_session", models.AiReview.session_id, models.AiReview.created_at),
]


def init_db(drop_first: bool = False) -> None:
    if drop_first:
        Base.metadata.drop_all(bind=engine)
        print("已删除所有旧表")
    Base.metadata.create_all(bind=engine)
    tables = sorted(Base.metadata.tables.keys())
    print(f"建表完成({len(tables)} 张): {', '.join(tables)}")


if __name__ == "__main__":
    init_db(drop_first="--drop" in sys.argv)

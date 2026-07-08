# -*- coding: utf-8 -*-
"""Repository 基类

约定 (ai-module-design §11):
- Repository 是 AI 模块触达数据库的唯一通道;
  context_builder / memory_retriever 只读, state_committer 只写。
- Repository 本身不 commit; 事务边界由调用方(state_committer / service)控制,
  以保证 §8.2 "同一事务按序写入、失败整体回滚"。
"""
from sqlalchemy.orm import Session


class BaseRepo:
    def __init__(self, db: Session):
        self.db = db

# -*- coding: utf-8 -*-
"""Repository 层 — AI 模块触达数据库的唯一通道 (ai-module-design §11)

调用方对照:
  context_builder / memory_retriever  -> 读: Session/Message/Clue/Fact/Npc
  state_committer                     -> 写: Message/ActionCheck/Clue/Fact/Task/AiReview/Session.update_meta
  clue_pressure                       -> ActionCheckRepo.count_failed_in_scene
  world_seed                          -> FactRepo(create, allow_protected=True) / NpcRepo.create_batch
"""
from .action_check_repo import ActionCheckRepo
from .ai_review_repo import AiReviewRepo
from .clue_repo import ClueRepo
from .fact_repo import FactRepo
from .message_repo import MessageRepo
from .npc_repo import NpcRepo
from .report_repo import ReportRepo
from .session_repo import SessionRepo
from .task_repo import TaskRepo

__all__ = [
    "ActionCheckRepo", "AiReviewRepo", "ClueRepo", "FactRepo",
    "MessageRepo", "NpcRepo", "ReportRepo", "SessionRepo", "TaskRepo",
]

# -*- coding: utf-8 -*-
"""服务层 — 数据库侧交付范围 (ai-module-design §3.3 / §3.7 / §5 / §8 / §11)

本包由数据库模块提供:
  memory_retriever  读: Fact 分层 / NPC Profile
  clue_pressure     算: 剧情推进压力 (§5.2)
  context_builder   读: 主/辅/开局/总结四类上下文组装
  state_committer   写: §8.1 校验 + §8.2 有序落库
  world_seed        写: 开局模组数据 (facts / npc_profiles)

Agent 层 (narrative/critic/...) 由 AI 模块同学在 app/ai/ 中实现,
通过上述接口读写数据库, 不得绕过。
"""
from . import (clue_pressure, context_builder, memory_retriever,
               state_committer, world_seed)

__all__ = ["clue_pressure", "context_builder", "memory_retriever",
           "state_committer", "world_seed"]

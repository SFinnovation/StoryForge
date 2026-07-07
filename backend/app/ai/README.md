# AI 模块

实现规格见 [docs/ai-module-design.md](../../docs/ai-module-design.md)。

## 模块结构

```
ai/
├── orchestrator.py       # 行动/开局编排入口
├── schemas/              # Pydantic 模型（待实现）
├── services/             # 各子模块（待实现）
├── prompts/              # Prompt 模板
└── tests/
```

## 调用关系

```
action_service → ai.orchestrator.handle_action()
                      → action_parser → rule_service → context_builder
                      → narrative_agent → critic_agent → revision_loop
                      → state_committer → repositories
```

## 环境变量

见根目录 `.env.example` 中 `AI_*` 段。

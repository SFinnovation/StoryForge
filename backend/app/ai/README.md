# AI 模块

设计文档：[docs/ai-module-design.md](../../../docs/ai-module-design.md)

## 模块结构

```
ai/
├── __init__.py              # get_ai_module() 入口
├── orchestrator.py          # AIModule 统一门面
├── schemas/                 # Pydantic 输入/输出模型
├── services/
│   ├── opening_agent.py     # OpeningAgent
│   ├── action_parser_agent.py
│   ├── narrative_agent.py
│   ├── critic_agent.py
│   ├── summary_agent.py
│   ├── revision_loop.py     # Narrative + Critic 修正循环
│   ├── llm_client.py
│   ├── fallbacks.py         # 无 API Key 时的 mock
│   └── ...
├── prompts/                 # Prompt 模板
└── schemas/*.schema.json    # JSON Schema（LLM 结构化输出）
```

## 五个 Agent 与调用方式

所有 Agent 方法（除 `generate_narrative`）返回 `AgentResult[T]`，含 `output`、`tokens_used`、`latency_ms`：

```python
from app.ai import get_ai_module
from app.ai.schemas import (
    OpeningInput, ActionParseInput, NarrativeInput, SummaryInput,
    CharacterCard, CheckResult,
)

ai = get_ai_module()

# 1. OpeningAgent — 开局剧情
result = await ai.generate_opening(OpeningInput(world="古堡悬疑", character=CharacterCard(...)))
text = result.output.display_text
print(result.tokens_used, result.latency_ms)

# 2. ActionParserAgent — 行动解析
parsed = await ai.parse_action(ActionParseInput(player_action="...", current_scene="..."))
# parsed.output.action_type, parsed.output.suggested_dc

# 3~4. NarrativeAgent + CriticAgent（含 RevisionLoop）
story = await ai.generate_narrative(NarrativeInput(...))
# story.display_text, story.review, story.tokens_used, story.latency_ms

# 5. SummaryAgent — 本局总结
report = await ai.generate_summary(SummaryInput(...))
```

## 后端行动 API

`POST /api/v1/sessions/{session_id}/action` 已通过 `action_service.handle_action()` 接入 AI 模块：

```json
{
  "action_text": "我想先观察大厅，看看有没有异常线索。"
}
```

响应含 `parsed_action`、`tokens_used`、`latency_ms`、`ai_review`、`next_options`。

## 与 action_service 的衔接

```
玩家行动
  → ai.parse_action()          # ActionParserAgent
  → rule_service.clamp_dc()    # 后端
  → dice_service.roll_check()  # 后端
  → ai.generate_narrative()    # Narrative + Critic + RevisionLoop
  → 落库 messages / clues / ai_reviews
```

## 本地联调（无需 LLM Key）

```bash
cd backend
pip install -r requirements.txt
python scripts/test_ai_module.py      # 五 Agent 单元联调
python scripts/bench_ai_module.py     # 性能基准
python scripts/test_action_api.py     # FastAPI 行动接口集成测试
```

未配置 `LLM_API_KEY` 时自动使用 `fallbacks.py` 中的 mock 响应（含古堡悬疑示例场景）。

## 环境变量

见根目录 `.env.example` 中 `LLM_*` 与 `AI_*` 段：

| 变量 | 默认 | 说明 |
|------|------|------|
| `LLM_API_KEY` | 空 | 为空则走 mock |
| `AI_MAX_REVISIONS` | 2 | Critic 驳回后最多重试次数 |
| `AI_CRITIC_PASS_SCORE` | 80 | 审核通过分数线 |
| `AI_ENABLE_CRITIC` | true | 关闭则跳过 Critic |
| `AI_FALLBACK_ON_CRITIC_FAIL` | true | 仍失败时使用保守兜底叙事 |

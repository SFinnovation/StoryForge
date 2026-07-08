# AI 模块

> **完整实现说明**：[docs/ai-module-implementation.md](../../../docs/ai-module-implementation.md)  
> **设计规格**：[docs/ai-module-design.md](../../../docs/ai-module-design.md)

## 快速入口

```python
from app.ai import get_ai_module

ai = get_ai_module()
```

## 五个 Agent

| Agent | 方法 | 返回类型 |
|-------|------|----------|
| OpeningAgent | `generate_opening()` | `AgentResult[OpeningOutput]` |
| ActionParserAgent | `parse_action()` | `AgentResult[ActionParseOutput]` |
| NarrativeAgent + Critic | `generate_narrative()` | `NarrativeWithReviewResult` |
| SummaryAgent | `generate_summary()` | `AgentResult[SummaryOutput]` |

## 后端编排（推荐）

业务代码通过 `app/services/` 调用，而非直接使用 Agent：

- `session_service.start_session()` → OpeningAgent
- `action_service.handle_action()` → ActionParser + Narrative + Critic
- `report_service.generate_report()` → SummaryAgent

## 本地测试

```bash
cd backend
python scripts/test_ai_module.py              # Agent 单元
python scripts/verify_implementation_spec.py  # 业务闭环
python scripts/verify_ai_db_interaction.py    # DB 交互
```

详细说明、DB 读写、API 格式、环境变量见 **[实现说明文档](../../../docs/ai-module-implementation.md)**。

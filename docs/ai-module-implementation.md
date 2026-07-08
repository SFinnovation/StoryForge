# StoryForge AI 模块 — 实现说明

> **版本**：v1.0 · **更新**：2026-07-08  
> **状态**：✅ MVP 已实现并接入后端  
> **设计规格**：[ai-module-design.md](ai-module-design.md)  
> **项目规格**：[implementation-spec.md](implementation-spec.md)

---

## 目录

1. [模块概览](#1-模块概览)
2. [总体架构与数据流](#2-总体架构与数据流)
3. [五个 Agent 说明](#3-五个-agent-说明)
4. [目录与文件结构](#4-目录与文件结构)
5. [后端集成层](#5-后端集成层)
6. [数据库交互](#6-数据库交互)
7. [REST API 对接](#7-rest-api-对接)
8. [环境变量与配置](#8-环境变量与配置)
9. [调用示例](#9-调用示例)
10. [修正循环与审核规则](#10-修正循环与审核规则)
11. [Mock 模式与兜底](#11-mock-模式与兜底)
12. [测试与验证](#12-测试与验证)
13. [实现状态对照表](#13-实现状态对照表)
14. [已知限制与后续计划](#14-已知限制与后续计划)

---

## 1. 模块概览

StoryForge AI 模块采用 **双 Agent + 修正循环** 架构，由 5 个专职 Agent 组成：

| Agent | 代码入口 | 触发时机 | 是否调用 LLM |
|-------|----------|----------|--------------|
| **OpeningAgent** | `generate_opening()` | 开局 `POST /sessions/start` | 是 |
| **ActionParserAgent** | `parse_action()` | 每次玩家行动 | 是 |
| **NarrativeAgent** | `generate_narrative()` | 检定完成后 | 是 |
| **CriticAgent** | 内嵌于 `RevisionLoop` | 每次叙事生成后 | 是 |
| **SummaryAgent** | `generate_summary()` | 结束本局生成报告 | 是 |

**硬约束（已实现）**：

- 骰子点数、成功判定由后端 `rule_service` 生成，AI **不得**修改
- Agent 不直接写数据库，仅输出 JSON 建议，由 `state_committer` 校验后落库
- Critic 可见 `hidden_truth` / `npc_private`，用于检测 NPC 信息泄露
- 判定失败时，叙事不得描述为完全成功

**统一入口**：

```python
from app.ai import get_ai_module

ai = get_ai_module()  # 单例
```

---

## 2. 总体架构与数据流

### 2.1 开局流程

```
POST /sessions/start
  → session_service.start_session()
  → context_builder.build_for_opening()     # 读 worlds + characters
  → ai_service.generate_opening()           # OpeningAgent
  → state_committer.commit_opening()        # 写 messages / tasks
  → world_seed.seed_session_world_data()    # 写 facts / npc_profiles
```

### 2.2 行动流程

```
POST /sessions/{id}/action
  → action_service.handle_action()
      ① context_builder.build_for_action()   # 读 DB 上下文
      ② ai.parse_action()                    # ActionParserAgent
      ③ rule_service.roll_check()            # 后端掷骰（非 LLM）
      ④ ai.generate_narrative()              # Narrative + Critic + RevisionLoop
      ⑤ state_committer.commit_action()      # 写 messages / checks / clues / facts / ai_reviews
      ⑥ clue_pressure.calculate()            # 更新 session 元数据
```

### 2.3 结束流程

```
POST /sessions/{id}/end
POST /sessions/{id}/report/generate
  → report_service.generate_report()
  → context_builder.build_for_summary()     # 聚合全局日志
  → ai_service.generate_summary()           # SummaryAgent
  → 写入 reports 表
```

### 2.4 架构图

```
┌──────────────┐     ┌─────────────────────────────────────────────┐
│   前端/API   │────►│  action_service / session_service /          │
│              │     │  report_service（编排层）                     │
└──────────────┘     └───────────┬─────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
  context_builder          ai_service              rule_service
  memory_retriever          (AIModule)              (d20 检定)
  clue_pressure                  │
         │                       ▼
         │              ┌────────────────┐
         │              │  OpeningAgent   │
         │              │  ActionParser   │
         │              │  NarrativeAgent │
         │              │  CriticAgent    │
         │              │  SummaryAgent   │
         │              │  RevisionLoop   │
         │              └────────┬───────┘
         │                       │ LLMClient (httpx 连接池)
         ▼                       ▼
  state_committer ──────► SQLite (facts / messages / clues / ...)
  fact_repository
  world_seed
```

---

## 3. 五个 Agent 说明

### 3.1 OpeningAgent — 开局剧情生成

| 项 | 说明 |
|----|------|
| **输入** | `OpeningInput`：世界观 + 角色卡 |
| **输出** | `AgentResult[OpeningOutput]`：`scene_title`、`narration`、`main_task`、`npcs` |
| **Prompt** | `backend/app/ai/prompts/opening.txt` |
| **示例场景** | 古堡悬疑：艾琳抵达黑鸦古堡，钟摆停止，老管家等候 |

```python
result = await ai.generate_opening(
    OpeningInput(
        world="古堡悬疑",
        character=CharacterCard(
            name="艾琳",
            profession="调查员",
            background="研究失踪案件的年轻侦探",
            motivation="寻找失踪学者留下的最后一份手稿",
        ),
    )
)
narration = result.output.display_text
```

### 3.2 ActionParserAgent — 行动解析

| 项 | 说明 |
|----|------|
| **输入** | `ActionParseInput`：玩家行动文本 + 当前场景 + 角色卡 |
| **输出** | `AgentResult[ActionParseOutput]` |
| **关键字段** | `action_type`、`skill_key`、`attribute_used`、`suggested_dc`、`needs_check` |
| **Prompt** | `backend/app/ai/prompts/action_parser.txt` |
| **不负责** | 掷骰、写剧情、改状态 |

```json
{
  "action_type": "investigate",
  "skill_key": "prc",
  "check_type": "观察",
  "attribute_used": "wisdom",
  "suggested_dc": 12,
  "needs_check": true,
  "reason": "玩家正在观察大厅环境，适合使用感知属性进行检定。"
}
```

### 3.3 NarrativeAgent — 主叙事

| 项 | 说明 |
|----|------|
| **输入** | `NarrativeInput`：玩家行动 + **后端给定** `check_result` + 场景/线索/clue_pressure |
| **输出** | `NarrativeWithReviewResult`（含 Critic 审核） |
| **Prompt** | `backend/app/ai/prompts/narrative_agent.txt` |
| **约束** | 不得修改 `success`/`dice_roll`；失败时只能给氛围和弱提示 |

判定失败时的叙事示例：

> 你举起手电扫过大厅……由于光线太暗，你没能发现更多细节。老管家轻声开口："客人，夜晚最好不要碰那座钟。"

### 3.4 CriticAgent — 辅审核

| 项 | 说明 |
|----|------|
| **输入** | 主叙事 JSON + 规则结果 + hidden_truth + npc_private |
| **输出** | `CriticOutput` |
| **Prompt** | `backend/app/ai/prompts/critic_agent.txt` |
| **六维评分** | rule_consistency、world_consistency、context_continuity、character_alignment、npc_knowledge_boundary、clue_progression |

```json
{
  "approved": true,
  "overall_score": 88,
  "scores": { "rule_consistency": 95, "world_consistency": 90, "...": "..." },
  "fatal_errors": [],
  "revision_instructions": []
}
```

**强制驳回条件**：

- `rule_consistency < 70`
- `npc_knowledge_boundary < 70`
- 存在 `fatal_errors`
- `overall_score < AI_CRITIC_PASS_SCORE`（默认 80）

### 3.5 SummaryAgent — 本局总结

| 项 | 说明 |
|----|------|
| **输入** | `SummaryInput`：全局玩家行动、检定结果、AI 旁白、已发现线索 |
| **输出** | `AgentResult[SummaryOutput]`：`story_summary`、`key_choices`、`next_suggestion` |
| **Prompt** | `backend/app/ai/prompts/report.txt` |
| **触发** | `POST /sessions/{id}/report/generate` |

---

## 4. 目录与文件结构

```
backend/app/ai/
├── __init__.py                 # 导出 get_ai_module()
├── orchestrator.py             # AIModule 统一门面
├── README.md                   # 模块速查（指向本文档）
│
├── schemas/                    # Pydantic 输入/输出模型
│   ├── character.py            # CharacterCard, WorldContext
│   ├── opening.py              # OpeningInput / OpeningOutput
│   ├── action_parse.py         # ActionParseInput / ActionParseOutput
│   ├── narrative.py            # NarrativeInput / NarrativeOutput / CheckResult
│   ├── critic.py               # CriticOutput / CriticScores
│   ├── summary.py              # SummaryInput / SummaryOutput
│   ├── agent_result.py         # AgentResult[T] 统一包装（含 metrics）
│   ├── narrative_output.schema.json
│   └── critic_output.schema.json
│
├── services/
│   ├── opening_agent.py
│   ├── action_parser_agent.py
│   ├── narrative_agent.py
│   ├── critic_agent.py
│   ├── summary_agent.py
│   ├── revision_loop.py        # Narrative + Critic 修正循环
│   ├── llm_client.py           # OpenAI 兼容客户端（连接池复用）
│   ├── prompt_loader.py        # Prompt 模板加载（带缓存）
│   ├── json_utils.py           # JSON 提取与 Pydantic 解析
│   └── fallbacks.py            # 无 API Key 时的 mock 响应
│
└── prompts/
    ├── opening.txt
    ├── action_parser.txt
    ├── narrative_agent.txt
    ├── critic_agent.txt
    ├── report.txt
    └── fallback_narration.txt  # Critic 多次失败后兜底叙事
```

**后端编排层**（`backend/app/services/`，非 `ai/` 包内）：

| 文件 | 职责 |
|------|------|
| `ai_service.py` | AI 模块门面，封装 `get_ai_module()` |
| `action_service.py` | 行动全流程编排 |
| `session_service.py` | 开局 / 结束 / 消息查询 |
| `report_service.py` | 本局总结 |
| `context_builder.py` | 从 DB 组装 AI 上下文 |
| `memory_retriever.py` | 读取 Fact / NPC Profile |
| `fact_repository.py` | 写入 AI 返回的 new_facts |
| `state_committer.py` | 校验后落库 |
| `world_seed.py` | 开局 seed 模组数据 |
| `rule_service.py` | D&D 5e 检定（非 LLM） |
| `clue_pressure.py` | 剧情推进压力计算 |

---

## 5. 后端集成层

### 5.1 推荐调用方式

后端业务代码 **不直接** 实例化 Agent，统一通过编排层：

```python
# 开局
from app.services.session_service import start_session

# 行动
from app.services.action_service import handle_action

# 总结
from app.services.report_service import generate_report
```

如需单独调试某个 Agent：

```python
from app.services.ai_service import get_ai_service

ai = get_ai_service()
result = await ai.parse_action(ActionParseInput(...))
```

### 5.2 AgentResult 与性能指标

除 `generate_narrative` 外，各方法返回 `AgentResult[T]`：

```python
@dataclass
class AgentResult(BaseModel, Generic[T]):
    output: T
    tokens_used: int = 0
    latency_ms: int = 0
```

`generate_narrative` 返回 `NarrativeWithReviewResult`，额外包含：

- `review`：Critic 审核结果
- `revision_count`：修正次数
- `used_fallback`：是否使用兜底叙事
- `tokens_used` / `latency_ms`：累计指标

---

## 6. 数据库交互

### 6.1 读取（Context Builder / Memory Retriever）

| 数据 | 来源表 | 用途 |
|------|--------|------|
| 世界观/模组 | `worlds` | `opening_prompt`、`description` → AI 世界观上下文 |
| 角色卡 | `characters` | 角色名/职业/动机 → `CharacterCard` |
| 属性修正 | `character_attributes` | `rule_service` 掷骰加值 |
| 已知线索 | `clues` | `known_clues` |
| 分层事实 | `facts` | `world_public` / `player_known` / `hidden_truth` / `npc_private` |
| NPC 配置 | `npc_profiles` | `visible_npcs`、知识边界 |
| 对话历史 | `messages` | `recent_summary` |
| 会话元数据 | `game_sessions` | `current_scene`、`clue_pressure` |

### 6.2 写入（State Committer / World Seed）

| 时机 | 写入表 | 内容 |
|------|--------|------|
| 开局 | `messages`、`tasks` | 开局旁白、主任务 |
| 开局 seed | `facts`、`npc_profiles` | 模组公开事实、隐藏真相、NPC 配置 |
| 每次行动 | `messages` | 玩家行动、骰子消息、AI 旁白 |
| 每次行动 | `action_checks` | 检定记录 |
| 每次行动 | `clues` | AI 返回的新线索（去重） |
| 每次行动 | `facts` | AI 返回的 `new_facts`（禁止 hidden→player 直升） |
| 每次行动 | `ai_reviews` | Critic 六维评分 |
| 每次行动 | `game_sessions` | 场景切换、summary、clue_pressure |
| 结束 | `reports` | SummaryAgent 生成的战报 |

### 6.3 Fact 分层（已实现）

| 类型 | 主 Agent 可见 | Critic 可见 | 写入时机 |
|------|---------------|-------------|----------|
| `world_public` | ✅ | ✅ | 开局 seed |
| `player_known` | ✅ | ✅ | AI `new_facts` / 后续扩展 |
| `hidden_truth` | ❌（仅摘要） | ✅ 完整 | 开局 seed |
| `npc_private` | ❌ | ✅ | 开局 seed |

### 6.4 规则书数据来源

| 数据 | 存储位置 | 说明 |
|------|----------|------|
| 技能/属性映射 | `rules/dnd5e/skills.json` | 文件，非 DB |
| 角色属性实例 | `character_attributes` 表 | 每角色一条 |
| 职业熟练技能 | `rule_service.PROFESSION_SKILLS` | 代码映射（MVP） |

---

## 7. REST API 对接

Base URL：`/api/v1` · 响应格式：`{ "code": 0, "message": "ok", "data": { ... } }`

| 方法 | 路径 | AI 模块参与 |
|------|------|-------------|
| POST | `/sessions/start` | OpeningAgent |
| POST | `/sessions/{id}/action` | ActionParser + Narrative + Critic |
| POST | `/sessions/{id}/end` | — |
| POST | `/sessions/{id}/report/generate` | SummaryAgent |
| GET | `/sessions/{id}/messages` | —（读持久化结果） |
| GET | `/sessions/{id}/meta` | clue_pressure |
| GET | `/sessions/{id}/facts?scope=player_known` | Fact 分层 |
| GET | `/sessions/{id}/ai-reviews` | Critic 记录 |

### 行动响应 `data` 结构

```json
{
  "player_message": { "id": 1, "content": "...", "message_type": "action" },
  "check": {
    "check_type": "观察",
    "skill_key": "prc",
    "attribute_used": "wisdom",
    "dc": 12,
    "dice_roll": 9,
    "ability_modifier": 3,
    "skill_bonus": 2,
    "final_value": 14,
    "is_success": true,
    "result_text": "d20(9) + 感知(+3) + 熟练(+2) = 14 ≥ DC 12，成功"
  },
  "story": {
    "message_id": 4,
    "narration": "...",
    "visible_result": "...",
    "new_clues": [],
    "next_options": ["询问管家", "转向东侧走廊"]
  },
  "session_meta": {
    "current_scene": "黑鸦古堡大厅",
    "clue_pressure": 0.08,
    "turns_since_key_clue": 1
  },
  "ai_review": {
    "approved": true,
    "overall_score": 88,
    "revision_count": 0,
    "used_fallback": false
  },
  "meta": { "tokens_used": 0, "latency_ms": 0 }
}
```

---

## 8. 环境变量与配置

见根目录 `.env.example`：

```env
# LLM（必填项：生产环境）
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=                        # 为空则使用 mock
LLM_MODEL=deepseek-chat
LLM_TIMEOUT=60
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7

# AI 模块
AI_MAX_REVISIONS=2                  # Critic 驳回后最多重试
AI_CRITIC_PASS_SCORE=80             # 审核通过分数线
AI_CRITIC_MODEL=                    # 可单独指定审核模型，默认同 LLM_MODEL
AI_ENABLE_CRITIC=true               # 关闭则跳过 Critic
AI_FALLBACK_ON_CRITIC_FAIL=true     # 仍失败则用 fallback_narration.txt
AI_CONTEXT_MESSAGE_LIMIT=20
```

配置加载：`backend/app/core/config.py` → `Settings`

---

## 9. 调用示例

### 9.1 完整古堡悬疑示例（Python 内部）

```python
from app.ai import get_ai_module
from app.ai.schemas import (
    OpeningInput, ActionParseInput, NarrativeInput, SummaryInput,
    CharacterCard, CheckResult,
)

ai = get_ai_module()
char = CharacterCard(
    name="艾琳", profession="调查员",
    background="研究失踪案件的年轻侦探",
    motivation="寻找失踪学者留下的最后一份手稿",
)

# 1. 开局
opening = await ai.generate_opening(OpeningInput(world="古堡悬疑", character=char))

# 2. 行动解析
parsed = await ai.parse_action(ActionParseInput(
    player_action="我想先观察大厅，看看有没有异常线索。",
    current_scene="黑鸦古堡大厅",
    character=char,
))

# 3. 叙事（假设后端已掷骰：失败）
story = await ai.generate_narrative(NarrativeInput(
    player_action="我想先观察大厅，看看有没有异常线索。",
    check_result=CheckResult(success=False, dice_roll=9, final_value=11, dc=12),
    current_scene="黑鸦古堡大厅",
    clue_pressure=0.2,
    world="古堡悬疑",
    character=char,
))

# 4. 本局总结
report = await ai.generate_summary(SummaryInput(
    world="古堡悬疑", character=char,
    player_actions=["观察大厅"], ai_narrations=[story.display_text],
))
```

### 9.2 HTTP 调用示例

```bash
# 开局
curl -X POST http://localhost:8000/api/v1/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"world_id": 2, "character_id": 1}'

# 行动
curl -X POST http://localhost:8000/api/v1/sessions/1/action \
  -H "Content-Type: application/json" \
  -d '{"action_text": "我想先观察大厅，看看有没有异常线索。"}'

# 生成报告
curl -X POST http://localhost:8000/api/v1/sessions/1/report/generate
```

---

## 10. 修正循环与审核规则

```
NarrativeAgent.generate()
    ↓
CriticAgent.review()
    ↓
approved? ──否──► revision_count < AI_MAX_REVISIONS?
    │                    │
   是                   是 → 携带 revision_instructions 重写
    │                    │
    │                   否 → fallback_narration.txt（若 AI_FALLBACK_ON_CRITIC_FAIL=true）
    ↓
返回 NarrativeWithReviewResult
```

| 场景 | LLM 调用次数（约） |
|------|-------------------|
| 最理想（一次过审） | parse(1) + narrative(1) + critic(1) = **3 次** |
| 修正 1 次 | **5 次** |
| 修正 2 次后 fallback | **7 次** |

---

## 11. Mock 模式与兜底

### 11.1 Mock 模式

当 `LLM_API_KEY` 为空时，各 Agent 自动使用 `fallbacks.py` 中的预设响应：

- 古堡悬疑开局旁白
- 「观察大厅」→ investigate / wisdom / DC 12
- 判定失败叙事 + 老管家警告
- Critic 评分 88 分通过
- 本局总结文本

便于无 API Key 时本地联调与 CI 验证。

### 11.2 兜底叙事

Critic 在 `AI_MAX_REVISIONS` 次修正后仍不通过，且 `AI_FALLBACK_ON_CRITIC_FAIL=true` 时：

- 使用 `prompts/fallback_narration.txt` 保守叙事
- `used_fallback=true`，不泄露关键线索

---

## 12. 测试与验证

```bash
cd backend
pip install -r requirements.txt

# 五 Agent 单元联调
python scripts/test_ai_module.py

# 完整业务闭环（开局→行动→结束→报告）
python scripts/verify_implementation_spec.py

# AI ↔ 数据库交互（规则书/模组/上下文/Fact）
python scripts/verify_ai_db_interaction.py

# FastAPI 行动接口集成
python scripts/test_action_api.py

# 接口性能基准（mock 路径）
python scripts/bench_ai_module.py
```

| 脚本 | 验证内容 |
|------|----------|
| `test_ai_module.py` | 五个 Agent 独立输出 + metrics |
| `verify_implementation_spec.py` | 文档 §8 完整闭环 |
| `verify_ai_db_interaction.py` | DB 读写、Fact 分层、NPC Profile |
| `test_action_api.py` | HTTP API 响应结构 |
| `bench_ai_module.py` | 接口层开销（mock < 0.05ms） |

---

## 13. 实现状态对照表

| 设计文档模块 | 设计文档章节 | 实现文件 | 状态 |
|-------------|-------------|----------|------|
| OpeningAgent | §3.8 | `opening_agent.py` | ✅ |
| ActionParserAgent | §3.1 | `action_parser_agent.py` | ✅ |
| NarrativeAgent | §3.4 | `narrative_agent.py` | ✅ |
| CriticAgent | §3.5 | `critic_agent.py` | ✅ |
| SummaryAgent | §3.8 | `summary_agent.py` | ✅ |
| RevisionLoop | §3.6 | `revision_loop.py` | ✅ |
| Context Builder | §3.3 | `context_builder.py` | ✅ |
| Memory Retriever | §11 | `memory_retriever.py` | ✅ |
| State Committer | §8 | `state_committer.py` | ✅ |
| Fact Repository | §11 | `fact_repository.py` | ✅ |
| clue_pressure | §5 | `clue_pressure.py` | ✅ |
| Rule Engine | §3.2 | `rule_service.py` | ✅ |
| AIModule 门面 | §9 | `orchestrator.py` | ✅ |
| action 编排 | §9.2 | `action_service.py` | ✅ |
| 开局 seed | §9.3 | `world_seed.py` | ✅ |
| Opening Critic | §9.3 P1 | — | ⏳ 未实现 |
| 流式输出 SSE | P3 | — | ⏳ 未实现 |
| JWT 认证 | P0 其他组 | demo user_id=1 | ⏳ 占位 |

---

## 14. 已知限制与后续计划

### 当前限制

1. **认证**：使用 `demo` 用户（`user_id=1`），JWT 待其他模块接入
2. **角色创建**：种子角色可用，`POST /characters` 待实现
3. **职业熟练**：`PROFESSION_SKILLS` 硬编码映射，未完全对接 D&D 5e `skills_json`
4. **Mock 模式**：`new_clues` 较少，配置 LLM 后才有丰富动态线索
5. **开局 Critic**：设计文档 P1 预留，当前开局不经 Critic 审核

### P1 后续

- [ ] Opening Critic 审核
- [ ] `npc_memories` 表读写
- [ ] 完整 `skills_json` 角色创建对接
- [ ] Critic 独立小模型（`AI_CRITIC_MODEL`）调优
- [ ] 前端 SSE 流式叙事

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-08 | 五 Agent 实现说明、DB 交互、API 对接、测试指南 |

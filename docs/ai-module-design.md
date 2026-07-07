# StoryForge AI 模块设计规格书

> **版本**：v1.0 · **更新**：2026-07-07  
> **负责人**：AI 模块  
> **读者**：AI / 后端 / 数据库 / 前端  
> **关联文档**：[implementation-spec.md](implementation-spec.md) · [dnd5e-integration.md](dnd5e-integration.md)

---

## 目录

1. [设计目标与原则](#1-设计目标与原则)
2. [总体架构](#2-总体架构)
3. [模块职责](#3-模块职责)
4. [记忆与 Fact 分层](#4-记忆与-fact-分层)
5. [clue_pressure 剧情推进压力](#5-clue_pressure-剧情推进压力)
6. [Agent 输入输出 Schema](#6-agent-输入输出-schema)
7. [修正循环与阈值](#7-修正循环与阈值)
8. [State Committer 状态提交器](#8-state-committer-状态提交器)
9. [后端内部接口（预留）](#9-后端内部接口预留)
10. [REST API 接口（前后端联调）](#10-rest-api-接口前后端联调)
11. [数据库读写接口（预留）](#11-数据库读写接口预留)
12. [目录结构与 Prompt 组织](#12-目录结构与-prompt-组织)
13. [MVP 范围与分期](#13-mvp-范围与分期)
14. [环境变量](#14-环境变量)
15. [联调检查清单](#15-联调检查清单)

---

## 1. 设计目标与原则

### 1.1 核心问题

AI 模块要解决的不是「让 AI 更会写故事」，而是：

| 问题 | 对策 |
|------|------|
| AI 乱写成功/失败 | 骰子与判定由 **Rule Engine（后端）** 强制执行 |
| AI 直接改 HP/线索/任务 | Agent 只输出 **建议变更**，由 **State Committer** 校验后落库 |
| NPC 全知全能 | **Fact 分层** + **npc_knowledge_boundary** 审核 |
| 上下文爆炸 / 记忆污染 | **Context Builder** 按可见性裁剪，不全量灌入 |
| 剧情原地绕圈 | **clue_pressure** 驱动弱→强线索引导 |

### 1.2 硬约束（不可违反）

```
1. 主 Agent / 辅 Agent 均不得生成 dice_roll、final_value、is_success
2. 主 Agent / 辅 Agent 均不得直接写数据库
3. 辅 Agent 可见 hidden_truth；主 Agent 默认不可见完整 hidden_truth
4. 判定失败时，叙事不得写成完全成功
5. 所有 Agent 输出必须为 JSON，经 Pydantic 校验
```

### 1.3 一句话架构

> **AI 负责生成与审核，后端负责规则与状态，数据库负责事实边界与记忆沉淀。**

---

## 2. 总体架构

```
玩家输入行动
    ↓
┌─────────────────────────────────────────────────────────────┐
│                    Action Orchestrator（后端）                 │
│  Action Parser → Rule Engine → Context Builder               │
│       → Narrative Agent → Critic Agent → Revision Loop       │
│       → State Committer → 持久化                              │
└─────────────────────────────────────────────────────────────┘
    ↓
返回：剧情 + 骰子卡片 + 线索更新 + 审核摘要（可选展示）
```

### 2.1 与旧版「单 Agent」对比

| 旧设计 | 新设计 |
|--------|--------|
| ai_service 一次生成 | 主 Agent + 辅 Agent + 修正循环 |
| 单一 facts 池 | world_public / player_known / hidden_truth / npc_private |
| 无审核 | Critic Agent 六维评分 + fatal_errors |
| AI 可能改状态 | State Committer 校验后才写入 |

---

## 3. 模块职责

### 3.1 Action Parser（行动解析器）

**职责**：自然语言 → 结构化行动。

**实现**：LLM + `rules/dnd5e/skills.json` 映射。

**不负责**：掷骰、改状态、写剧情。

### 3.2 Rule Engine（规则判定器）

**职责**：d20、DC 钳制、属性修正、熟练加值、成功判定。

**实现**：纯后端 `rule_service` + `dice_service`（**非 LLM**）。

### 3.3 Context Builder（上下文构建器）

**职责**：从 DB 读取并按可见性组装主/辅 Agent 上下文；计算 `clue_pressure`。

**不负责**：调用 LLM。

### 3.4 Narrative Agent（主叙事 Agent）

**职责**：根据 **已确定的** `rule_result` 生成本轮剧情 JSON。

### 3.5 Critic Agent（辅审核 Agent）

**职责**：审查主 Agent 输出；输出评分、`fatal_errors`、`revision_instructions`。

**特权**：可见 `hidden_truths`、`npc_private_facts`（用于检测泄露）。

### 3.6 Revision Loop（修正循环）

**职责**：`approved=false` 时携带 `revision_instructions` 要求主 Agent 重写；**最多 2 次**。

**兜底**：仍失败则使用 `fallback_narration` 保守模板。

### 3.7 State Committer（状态提交器）

**职责**：校验 `state_updates` 合法性 → 写入 messages / clues / facts / tasks / action_checks / ai_reviews。

**Agent 不可绕过此模块写库。**

### 3.8 Summary Agent（本局总结）

**职责**：会话结束时生成 `reports` 表内容（P0 必做）。

---

## 4. 记忆与 Fact 分层

### 4.1 Fact 类型（MVP 三类，P1 扩展两类）

| 类型 | 代码 | 主 Agent 可见 | 辅 Agent 可见 | 前端可见 |
|------|------|---------------|---------------|----------|
| 世界公开事实 | `world_public` | ✅ | ✅ | ✅（世界观页） |
| 玩家已知事实 | `player_known` | ✅ | ✅ | ✅ |
| 隐藏真相 | `hidden_truth` | ⚠️ 摘要+禁止透露 | ✅ 完整 | ❌ |
| NPC 私有事实 | `npc_private` | ❌（P1） | ✅ | ❌ |
| 会话已发生 | `session_fact` | ✅ | ✅ | 部分 |
| 临时状态 | `temporary` | ✅ | ✅ | 部分 |

### 4.2 Fact 数据结构

```json
{
  "fact_id": "fact_001",
  "session_id": 12,
  "content": "地下室入口位于东侧走廊尽头的画像后。",
  "fact_type": "hidden_truth",
  "visibility_json": {
    "player": false,
    "npcs": ["butler_001", "lord_001"],
    "dm": true
  },
  "related_scene": "east_corridor",
  "importance": "key",
  "status": "locked"
}
```

`status` 枚举：`locked | active | resolved`

### 4.3 NPC Profile（MVP 简化）

不建独立 NPC Agent，用 `npc_profiles` 表约束主 Agent 中 NPC 对话：

```json
{
  "npc_id": "butler_001",
  "name": "老管家",
  "personality": "谨慎、回避、忠诚于古堡主人",
  "knowledge_scope": ["古堡日常", "地下室钥匙", "学者昨晚进东侧走廊"],
  "forbidden_knowledge": ["最终 Boss 身份", "密室机关完整解法"],
  "speaking_style": "礼貌、含糊、敬语"
}
```

---

## 5. clue_pressure 剧情推进压力

### 5.1 含义

不是「线索衰减」，而是系统判断：**玩家是否长时间未获得有效推进**，从而调整 AI 给出暗示的强度。

### 5.2 计算公式（MVP）

```python
def calc_clue_pressure(
    turns_since_key_clue: int,
    failed_checks_in_scene: int,
    player_confusion_score: float = 0.0,
) -> float:
    return min(1.0, turns_since_key_clue * 0.15 + failed_checks_in_scene * 0.1 + player_confusion_score * 0.2)
```

### 5.3 行为档位

| clue_pressure | 主 Agent 行为 |
|---------------|---------------|
| 0.0 – 0.3 | 正常反馈，不主动塞线索 |
| 0.3 – 0.6 | 环境暗示、弱线索 |
| 0.6 – 0.8 | 明显线索，引导换方向 |
| 0.8 – 1.0 | 强推进，允许 NPC 主动提示或触发事件 |

### 5.4 持久化

写入 `game_sessions.clue_pressure`（浮点）及 `turns_since_key_clue`（整数），每轮 action 后更新。

---

## 6. Agent 输入输出 Schema

### 6.1 Action Parser 输出

```json
{
  "action_type": "stealth_move",
  "skill_key": "ste",
  "check_type": "隐匿",
  "attribute_used": "dexterity",
  "suggested_dc": 15,
  "needs_check": true,
  "target": "guard",
  "intent": "绕过守卫并前往走廊尽头",
  "reason": "玩家试图潜行绕过守卫"
}
```

### 6.2 Rule Engine 输出（后端生成，非 LLM）

```json
{
  "check_type": "隐匿",
  "skill_key": "ste",
  "attribute_used": "dexterity",
  "dc": 15,
  "dice_roll": 7,
  "ability_modifier": 3,
  "skill_bonus": 2,
  "final_value": 12,
  "is_success": false,
  "result_text": "d20(7) + 敏捷(+3) + 熟练(+2) = 12 < DC 15，失败"
}
```

### 6.3 Context Builder 输出 — 主 Agent 包

```json
{
  "role": "NarrativeAgent",
  "world_style": "哥特悬疑",
  "public_world_facts": [],
  "current_scene": { "name": "古堡东侧走廊", "description": "..." },
  "player_card": { "name": "艾琳", "class_id": "rogue", "skills": {} },
  "recent_summary": "玩家已进入古堡大厅，尚未发现地下室。",
  "recent_messages": [],
  "player_known_clues": [],
  "visible_npcs": [],
  "player_action": "我想偷偷绕过守卫。",
  "rule_result": {},
  "clue_pressure": 0.65,
  "forbidden": [
    "不得透露 hidden_truth 中未解锁内容",
    "不得修改骰子结果",
    "不得替玩家做重大决定",
    "NPC 不得超出 knowledge_scope"
  ]
}
```

### 6.4 Narrative Agent 输出

```json
{
  "narration": "你压低脚步，但靴底踩碎枯叶。守卫猛地转身，手按剑柄。",
  "visible_result": "潜行失败，守卫产生警觉。",
  "new_clues": [
    {
      "title": "东侧走廊的冷风",
      "content": "在被发现前，你感到走廊尽头吹来异常寒冷的风。",
      "importance": "normal",
      "visibility": "player_known"
    }
  ],
  "state_updates": {
    "scene": "古堡东侧走廊入口",
    "summary_delta": "潜行失败，守卫警觉。",
    "hp_delta": 0,
    "npc_alertness": [{ "npc_id": "guard_001", "delta": 2 }],
    "task_updates": [],
    "new_facts": []
  },
  "next_options": ["尝试解释", "立刻逃跑", "观察守卫身后的门"]
}
```

### 6.5 Critic Agent 输出

```json
{
  "approved": false,
  "overall_score": 72,
  "scores": {
    "rule_consistency": 60,
    "world_consistency": 85,
    "context_continuity": 70,
    "character_alignment": 80,
    "npc_knowledge_boundary": 50,
    "clue_progression": 75
  },
  "fatal_errors": [
    "主 Agent 写成了成功绕过守卫，但 rule_result.is_success 为 false"
  ],
  "revision_instructions": [
    "必须体现潜行失败",
    "可给补救机会，但不能直接进入目标房间",
    "守卫不得说出地下室真相"
  ]
}
```

### 6.6 Summary Agent 输出

与 [implementation-spec §9.5](implementation-spec.md) 一致。

---

## 7. 修正循环与阈值

### 7.1 流程

```
Narrative Agent 生成
  → Critic Agent 审核
  → approved=true → State Committer
  → approved=false 且 revision_count < 2 → 带 revision_instructions 重写
  → 仍失败 → fallback_narration
```

### 7.2 通过阈值

| 条件 | 结果 |
|------|------|
| `overall_score >= 80` 且 `fatal_errors` 为空 | 通过 |
| `overall_score` 60–79 | 修正 1 次 |
| `overall_score < 60` 或存在 `fatal_errors` | 必须重写 |
| `rule_consistency < 70` | 强制重写 |
| `npc_knowledge_boundary < 70` | 强制重写 |

### 7.3 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `AI_MAX_REVISIONS` | 2 | 最大修正次数 |
| `AI_CRITIC_PASS_SCORE` | 80 | 审核通过分数线 |
| `AI_CRITIC_MODEL` | 同 LLM_MODEL | 可单独指定审核模型 |

---

## 8. State Committer 状态提交器

### 8.1 校验规则

| 检查项 | 规则 |
|--------|------|
| HP | `hp + hp_delta >= 0` 且 `<= max_hp` |
| 线索 | 不重复 `title`；`key` 线索需 `clue_pressure >= 0.6` 或判定成功 |
| hidden_truth | `new_facts` 不得将 `hidden_truth` 直接设为 `player_known` |
| 规则一致 | `is_success=false` 时 narration 不得描述完全成功 |
| NPC 警觉 | `delta` 单次不超过 3 |
| 场景 | 仅允许合理相邻场景切换 |

### 8.2 写入顺序（同一事务）

```
1. messages (player action)
2. action_checks (若有检定)
3. messages (system dice)
4. messages (ai narration) + tokens_used / latency_ms
5. clues (new_clues)
6. facts (state_updates.new_facts)
7. tasks (task_updates)
8. game_sessions (scene, summary, clue_pressure)
9. ai_reviews (审核记录)
10. npc_memories (P1，若有 NPC 相关更新)
```

---

## 9. 后端内部接口（预留）

> **约定**：以下接口由 `backend/app/ai/` 实现，供 `session_service` / `action_service` 调用。  
> **命名空间**：Python 模块路径，非 HTTP。

### 9.1 接口一览

| 模块 | 方法 | 输入 | 输出 |
|------|------|------|------|
| `action_parser` | `parse(session_id, action_text)` | `str` | `ActionParseResult` |
| `context_builder` | `build_for_narrative(session_id, rule_result, action_text)` | — | `NarrativeContext` |
| `context_builder` | `build_for_critic(session_id, narrative_output, rule_result)` | — | `CriticContext` |
| `clue_pressure` | `calculate(session_id)` | — | `CluePressureResult` |
| `memory_retriever` | `get_player_known_facts(session_id)` | — | `list[Fact]` |
| `memory_retriever` | `get_hidden_truths(session_id)` | — | `list[Fact]` |
| `narrative_agent` | `generate(context)` | `NarrativeContext` | `NarrativeOutput` |
| `narrative_agent` | `revise(context, previous, instructions)` | — | `NarrativeOutput` |
| `critic_agent` | `review(critic_context, narrative_output)` | — | `CriticOutput` |
| `revision_loop` | `run(narrative_fn, critic_fn, context)` | — | `RevisionResult` |
| `state_committer` | `commit(session_id, narrative, check, review)` | — | `CommitResult` |
| `summary_agent` | `generate_report(session_id)` | — | `ReportOutput` |
| `ai_orchestrator` | `handle_action(session_id, user_id, action_text)` | — | `ActionResponse` |

### 9.2 `ai_orchestrator.handle_action` 伪代码

```python
async def handle_action(session_id: int, user_id: int, action_text: str) -> ActionResponse:
    session = session_repo.get_playing(session_id, user_id)

    parsed = await action_parser.parse(session_id, action_text)
    check = None
    if parsed.needs_check:
        check = rule_service.roll_check(session.character, parsed)

    clue_pressure = clue_pressure_service.calculate(session_id)
    ctx = context_builder.build_for_narrative(session_id, check, action_text, clue_pressure)

    revision = await revision_loop.run(
        generate=lambda: narrative_agent.generate(ctx),
        review=lambda out: critic_agent.review(
            context_builder.build_for_critic(session_id, out, check), out
        ),
        max_revisions=settings.AI_MAX_REVISIONS,
    )

    commit_result = state_committer.commit(
        session_id, revision.output, check, revision.final_review
    )
    return ActionResponse.from_commit(commit_result, check, revision)
```

### 9.3 开局流程内部接口

| 方法 | 说明 |
|------|------|
| `context_builder.build_for_opening(world_id, character_id)` | 开局上下文 |
| `narrative_agent.generate_opening(context)` | 开局 JSON（无检定） |
| `critic_agent.review_opening(context, output)` | 开局审核（可选 P1） |
| `state_committer.commit_opening(session_id, output)` | 写入初始 messages / tasks / facts |

---

## 10. REST API 接口（前后端联调）

> Base URL：`/api/v1` · 认证：`Bearer Token`  
> 完整错误码见 [implementation-spec §7.3](implementation-spec.md)

### 10.1 核心：提交行动（扩展响应）

**`POST /api/v1/sessions/{session_id}/action`**

**请求**：

```json
{
  "action_text": "我想偷偷绕过守卫。"
}
```

**响应 `data`（扩展字段标注 🆕）**：

```json
{
  "code": 0,
  "data": {
    "player_message": {
      "id": 101,
      "content": "我想偷偷绕过守卫。",
      "message_type": "action",
      "created_at": "2026-07-07T12:00:00Z"
    },
    "check": {
      "id": 55,
      "check_type": "隐匿",
      "skill_key": "ste",
      "attribute_used": "dexterity",
      "dc": 15,
      "dice_roll": 7,
      "ability_modifier": 3,
      "skill_bonus": 2,
      "final_value": 12,
      "is_success": false,
      "result_text": "d20(7) + 敏捷(+3) + 熟练(+2) = 12 < DC 15，失败"
    },
    "story": {
      "message_id": 103,
      "narration": "你压低脚步，但靴底踩碎枯叶。守卫猛地转身……",
      "visible_result": "潜行失败，守卫产生警觉。",
      "new_clues": [],
      "task_updates": [],
      "next_options": ["尝试解释", "立刻逃跑", "观察守卫身后的门"]
    },
    "session_meta": {
      "current_scene": "古堡东侧走廊入口",
      "clue_pressure": 0.45,
      "turns_since_key_clue": 2
    },
    "ai_review": {
      "approved": true,
      "overall_score": 86,
      "revision_count": 0,
      "used_fallback": false
    },
    "meta": {
      "tokens_used": 1240,
      "latency_ms": 3200
    }
  }
}
```

**前端使用说明**：

| 字段 | 组件 |
|------|------|
| `check` | `DiceResultCard.vue` |
| `story.narration` | `StoryMessage.vue`（打字机效果） |
| `story.new_clues` | 刷新 `CluePanel` |
| `story.next_options` | 快捷行动按钮（可选） |
| `ai_review` | P1：`ReviewBadge.vue` 答辩展示 |
| `session_meta.clue_pressure` | P1：管理端 / 调试面板 |

### 10.2 开局（扩展）

**`POST /api/v1/sessions/start`**

响应 `data.opening` 增加：

```json
{
  "opening": {
    "scene_title": "雾中的古堡",
    "narration": "...",
    "main_task": "调查失踪学者",
    "initial_clues": [],
    "visible_npcs": [
      { "npc_id": "butler_001", "name": "老管家", "description": "神情紧张" }
    ],
    "ai_review": { "approved": true, "overall_score": 88 }
  }
}
```

### 10.3 获取玩家已知 Fact（预留 · P1）

**`GET /api/v1/sessions/{session_id}/facts?scope=player_known`**

```json
{
  "code": 0,
  "data": {
    "facts": [
      {
        "fact_id": "fact_010",
        "content": "学者最后出现在古堡大厅。",
        "fact_type": "player_known",
        "related_scene": "main_hall",
        "importance": "important",
        "status": "active"
      }
    ]
  }
}
```

### 10.4 获取 clue_pressure（预留 · P1 调试）

**`GET /api/v1/sessions/{session_id}/meta`**

```json
{
  "code": 0,
  "data": {
    "clue_pressure": 0.65,
    "turns_since_key_clue": 4,
    "failed_checks_in_scene": 2,
    "current_scene": "east_corridor"
  }
}
```

### 10.5 获取 AI 审核记录（预留 · P1 答辩）

**`GET /api/v1/sessions/{session_id}/ai-reviews?limit=10`**

```json
{
  "code": 0,
  "data": {
    "reviews": [
      {
        "id": 8,
        "message_id": 103,
        "approved": true,
        "overall_score": 86,
        "scores": {
          "rule_consistency": 90,
          "world_consistency": 85,
          "context_continuity": 82,
          "character_alignment": 88,
          "npc_knowledge_boundary": 85,
          "clue_progression": 80
        },
        "revision_count": 0,
        "created_at": "2026-07-07T12:00:03Z"
      }
    ]
  }
}
```

### 10.6 本局总结（不变，走 Summary Agent）

**`POST /api/v1/sessions/{session_id}/report/generate`**

### 10.7 前端 Pinia 扩展（预留）

```typescript
interface SessionState {
  currentSession: Session | null
  messages: Message[]
  clues: Clue[]
  tasks: Task[]
  facts: Fact[]              // 🆕 player_known
  sessionMeta: SessionMeta | null  // 🆕 clue_pressure 等
  lastAiReview: AiReview | null    // 🆕
  isSubmitting: boolean
}
```

### 10.8 前端 API 封装（预留）

```typescript
// frontend/src/api/session.ts
export const submitAction = (sessionId: number, actionText: string) =>
  http.post(`/sessions/${sessionId}/action`, { action_text: actionText })

export const getSessionMeta = (sessionId: number) =>
  http.get(`/sessions/${sessionId}/meta`)

export const getPlayerFacts = (sessionId: number) =>
  http.get(`/sessions/${sessionId}/facts`, { params: { scope: 'player_known' } })

export const getAiReviews = (sessionId: number, limit = 10) =>
  http.get(`/sessions/${sessionId}/ai-reviews`, { params: { limit } })
```

---

## 11. 数据库读写接口（预留）

> **约定**：由 `backend/app/repositories/` 实现，供 `context_builder` / `state_committer` 调用。  
> 表名与 [数据库存储结构设计.sql](../数据库存储结构设计.sql) 及下文扩展表一致。

### 11.1 Repository 一览

| Repository | 方法 | 调用方 |
|------------|------|--------|
| `SessionRepo` | `get_playing(session_id, user_id)` | orchestrator |
| `SessionRepo` | `update_meta(session_id, scene, summary, clue_pressure, turns)` | state_committer |
| `MessageRepo` | `list_recent(session_id, limit=20)` | context_builder |
| `MessageRepo` | `create(...)` | state_committer |
| `ClueRepo` | `list_by_session(session_id)` | context_builder |
| `ClueRepo` | `create_batch(...)` | state_committer |
| `FactRepo` | `list_by_session(session_id, fact_types[], visibility)` | memory_retriever |
| `FactRepo` | `create(...)` / `unlock(fact_id)` | state_committer |
| `NpcRepo` | `list_visible(session_id, scene)` | context_builder |
| `ActionCheckRepo` | `create(...)` | state_committer |
| `ActionCheckRepo` | `count_failed_in_scene(session_id, scene)` | clue_pressure |
| `AiReviewRepo` | `create(...)` | state_committer |
| `AiReviewRepo` | `list_recent(session_id, limit)` | API GET ai-reviews |
| `TaskRepo` | `update_batch(...)` | state_committer |

### 11.2 新增表（AI 模块）

见 [数据库存储结构设计.sql](../数据库存储结构设计.sql) 末尾 `§11 AI 模块扩展表`，或 implementation-spec §6 更新段。

**核心新增**：

- `facts` — Fact 分层存储
- `npc_profiles` — NPC 人格与知识边界
- `ai_reviews` — 辅 Agent 审核记录
- `game_sessions` 扩展字段：`clue_pressure`、`turns_since_key_clue`

---

## 12. 目录结构与 Prompt 组织

```
backend/app/ai/
├── __init__.py
├── orchestrator.py          # handle_action / handle_opening
├── schemas/
│   ├── action_parse.py    # Pydantic models
│   ├── narrative.py
│   ├── critic.py
│   └── context.py
├── services/
│   ├── action_parser.py
│   ├── context_builder.py
│   ├── narrative_agent.py
│   ├── critic_agent.py
│   ├── revision_loop.py
│   ├── state_committer.py
│   ├── clue_pressure.py
│   ├── memory_retriever.py
│   └── summary_agent.py
├── prompts/
│   ├── action_parser.txt
│   ├── narrative_agent.txt
│   ├── critic_agent.txt
│   ├── opening.txt
│   ├── report.txt
│   └── fallback_narration.txt
└── tests/
    ├── test_rule_consistency.py
    ├── test_npc_boundary.py
    └── test_clue_pressure.py
```

Prompt 模板见 `backend/app/ai/prompts/` 目录内文件。

---

## 13. MVP 范围与分期

### P0（答辩必做）

- [x] 文档：双 Agent 架构 + 接口预留
- [ ] Action Parser + Rule Engine 联调
- [ ] Narrative Agent + Critic Agent + Revision Loop（max 2）
- [ ] State Committer 基础校验
- [ ] facts 三类：`world_public` / `player_known` / `hidden_truth`
- [ ] clue_pressure 计算与注入
- [ ] `ai_reviews` 落库
- [ ] Summary Agent 战报

### P1（加分）

- [ ] `GET /sessions/{id}/meta`、`/facts`、`/ai-reviews`
- [ ] 前端 ReviewBadge / 调试面板
- [ ] `npc_profiles` + `npc_private` fact
- [ ] 开局 Critic 审核

### P2（不做）

- 向量 RAG、多 NPC 独立 Agent、复杂关系值

---

## 14. 环境变量

在根目录 `.env` 追加：

```env
# AI 模块
AI_MAX_REVISIONS=2
AI_CRITIC_PASS_SCORE=80
AI_CRITIC_MODEL=                    # 空则同 LLM_MODEL
AI_CONTEXT_MESSAGE_LIMIT=20         # Context Builder 最近消息条数
AI_ENABLE_CRITIC=true               # false 时跳过审核（仅调试）
AI_FALLBACK_ON_CRITIC_FAIL=true     # 审核仍失败时用保底叙事
```

---

## 15. 联调检查清单

### AI ↔ 后端

- [ ] `action_parser` 输出 `skill_key` 可被 `rule_service` 消费
- [ ] `rule_result.is_success` 传入 Narrative Context
- [ ] Critic 驳回后 `revision_instructions` 进入第二轮 Prompt
- [ ] `state_committer` 拒绝非法 `hp_delta` 时整事务回滚

### 后端 ↔ 数据库

- [ ] 每轮 action 写入 `action_checks` + `ai_reviews`
- [ ] `clue_pressure` 回写 `game_sessions`
- [ ] `hidden_truth` 不通过 commit 直接变为 `player_known`

### 前端 ↔ 后端

- [ ] `POST /action` 返回 `check` + `story` + `ai_review`
- [ ] 提交中 `isSubmitting=true` 防重复
- [ ] 401 / 50301 有统一错误提示

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-07 | 双 Agent 架构、Fact 分层、接口预留 |

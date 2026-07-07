# StoryForge 灵境档案 — 实现规格书

> **版本**：v1.0 · **更新**：2026-07-07  
> **读者**：前端 / 后端 / AI / 数据库 / 答辩展示  
> **目标**：5 天内交付可演示的 MVP，形成「角色创建 → AI 开局 → 行动判定 → 剧情推进 → 本局总结」完整闭环。

---

## 目录

1. [项目定位与边界](#1-项目定位与边界)
2. [技术栈与仓库结构](#2-技术栈与仓库结构)
3. [MVP 范围与验收标准](#3-mvp-范围与验收标准)
4. [核心状态机](#4-核心状态机)
5. [规则引擎（D&D 5e 整合）](#5-规则引擎dnd-5e-整合)
6. [数据模型](#6-数据模型)
7. [API 规范](#7-api-规范)
8. [核心业务流程](#8-核心业务流程)
9. [AI 模块规范](#9-ai-模块规范)
10. [前端实现清单](#10-前端实现清单)
11. [后端实现清单](#11-后端实现清单)
12. [环境配置与本地启动](#12-环境配置与本地启动)
13. [五天开发里程碑](#13-五天开发里程碑)
14. [测试与答辩演示脚本](#14-测试与答辩演示脚本)
15. [附录](#15-附录)

---

## 1. 项目定位与边界

### 1.1 一句话定义

StoryForge 不是普通 AI 聊天，而是 **AI 叙事 + d20 规则判定 + 会话持久化** 的轻量化单人跑团 Web 平台。

### 1.2 核心闭环

```
选择世界观 → 创建角色 → AI 生成开局
    → 玩家输入行动 → 系统掷骰判定 → AI 推进剧情
    → 记录日志/线索 → 生成本局总结
```

### 1.3 做什么 / 不做什么

| 做（MVP 范围内） | 不做（二期或超出范围） |
|------------------|------------------------|
| 单人 AI 主持跑团 | 完整 Foundry 级规则引擎 |
| **D&D 5e SRD**：属性/技能/熟练加值/d20 检定 | 复杂战斗网格、完整法术列表、多职业升级树 |
| 种族 / 职业 / 背景角色创建 | 多人实时同房 WebSocket 跑团 |
| 自由输入 + 快捷行动按钮 | 语音、3D 地图、模组编辑器 |
| 会话日志、线索、任务、结局报告 | 商业化支付、复杂 RBAC |

### 1.4 与竞品差异

| 产品 | 侧重点 | 本项目差异 |
|------|--------|------------|
| SillyTavern / KoboldAI | AI 角色扮演 | 本项目有 **规则化骰子判定** 与结构化日志 |
| Avrae / FoundryVTT | 传统跑团工具 | 本项目 **AI 自动生成剧情与总结**，上手更轻 |
| 通用 Chatbot | 对话 + 存储 | 本项目形成 **角色卡 → 判定 → 线索 → 战报** 闭环 |

---

## 2. 技术栈与仓库结构

### 2.1 技术选型（已确定）

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3 + Vue Router + Pinia | 组件化页面，Pinia 管理会话状态 |
| UI | Element Plus 或 Naive UI | 表单、布局、表格 |
| 图表 | ECharts | 属性雷达图、判定统计、结局分布 |
| 后端 | FastAPI + SQLAlchemy | REST API，Pydantic 校验 |
| 数据库 | SQLite（开发）/ MySQL（部署可选） | MVP 优先 SQLite，零配置 |
| 认证 | JWT | 简单 Bearer Token |
| AI | OpenAI 兼容 API | 通义 / DeepSeek / OpenAI 均可 |

### 2.2 推荐 monorepo 结构

```
StoryForge/
├── frontend/
│   ├── src/
│   │   ├── views/          # 页面
│   │   ├── components/     # 业务组件
│   │   ├── api/            # axios 封装
│   │   ├── stores/         # Pinia
│   │   └── router/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/            # 路由层
│   │   ├── services/       # 业务逻辑
│   │   ├── models/         # ORM 模型
│   │   ├── schemas/        # Pydantic
│   │   ├── core/           # 配置、安全、依赖
│   │   └── prompts/        # AI Prompt 模板
│   ├── requirements.txt
│   └── alembic/            # 可选：数据库迁移
├── rules/
│   └── dnd5e/              # 从 Foundry dnd5e 包提取的 SRD JSON
├── scripts/
│   └── extract_dnd5e_rules.py
├── docs/
│   ├── implementation-spec.md   # 本文档
│   ├── dnd5e-integration.md     # D&D 5e 整合说明
│   └── architecture.md
├── .env.example
└── README.md
```

### 2.3 模块依赖关系

```
frontend ──HTTP──► api (FastAPI)
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
   auth_service  session_service  ai_service
         │            │            │
         └────────────┼────────────┘
                      ▼
              rule_service / dice_service
                      │
                      ▼
                   database
```

**原则**：骰子点数、属性修正、成功判定 **必须由后端 `dice_service` 生成**，AI 只负责理解行动与生成叙事。

---

## 3. MVP 范围与验收标准

### 3.1 P0 — 必须完成（答辩最小路径）

| # | 功能 | 负责模块 | 验收标准 |
|---|------|----------|----------|
| 1 | 用户注册/登录 | 后端 auth + 前端 Login | 能拿到 JWT，访问受保护接口 |
| 2 | 世界观列表与选择 | worlds API + WorldSelectView | 至少 2 个内置世界观可选 |
| 3 | 角色创建（D&D 5e：种族/职业/背景/属性/技能） | characters API + CharacterCreateView | 属性含种族加值，技能熟练写入 DB |
| 4 | 开始新局 + AI 开局 | sessions/start + ai_service | 进入 play 页，看到开局旁白与主任务 |
| 5 | 玩家行动 + d20 判定 | sessions/{id}/action | 返回检定卡片 + AI 后续剧情 |
| 6 | 消息与判定持久化 | messages + action_checks 表 | 刷新页面后可拉取历史 |
| 7 | 结束本局 + AI 总结 | report/generate | 跳转报告页，展示摘要与结局类型 |
| 8 | 跑团主界面三栏布局 | GameSessionView | 左状态 / 中对话 / 右骰子与日志 |

### 3.2 P1 — 建议完成（加分项）

| # | 功能 | 验收标准 |
|---|------|----------|
| 1 | 线索面板 | 判定成功后 `new_clues` 写入并展示 |
| 2 | 任务面板 | 任务状态随 `task_updates` 变化 |
| 3 | 历史档案页 | 列出已完成 sessions，可查看报告 |
| 4 | 报告页 ECharts | 雷达图 + 成功/失败饼图 |
| 5 | 管理端统计 | 会话数、世界观热度、判定成功率 |
| 6 | 游客模式（可选） | 免登录本地 session，答辩备用 |

### 3.3 P2 — 后续扩展

- WebSocket 多人同房
- 自定义世界观编辑器
- 完整战斗轮（先攻、AC、伤害骰）
- 升级与技能树
- 导出 PDF 战报

---

## 4. 核心状态机

### 4.1 会话（Session）状态

```
                    POST /sessions/start
  ┌─────────┐  ──────────────────────►  ┌─────────┐
  │ (无)    │                           │ playing │
  └─────────┘                           └────┬────┘
                                             │
                              POST /sessions/{id}/end
                              或 report/generate
                                             ▼
                                        ┌──────────┐
                                        │ finished │
                                        └────┬─────┘
                                             │ 用户归档（可选）
                                             ▼
                                        ┌──────────┐
                                        │ archived │
                                        └──────────┘
```

**约束**：
- 仅 `playing` 状态可提交 `/action`
- `finished` 后禁止继续行动，可重新查看报告
- 同一用户同时仅允许 **1 个** `playing` session（MVP 简化）

### 4.2 单次行动处理状态（后端内部）

```
RECEIVED → CONTEXT_LOADED → AI_PARSED → DICE_ROLLED
    → CHECK_SAVED → AI_NARRATED → PERSISTED → RESPONSE
```

任一步失败应回滚事务，并返回统一错误格式（见 §7.3）。

---

## 5. 规则引擎（D&D 5e 整合）

> 详细说明见 [dnd5e-integration.md](dnd5e-integration.md)。规则数据位于 `rules/dnd5e/*.json`，由 `scripts/extract_dnd5e_rules.py` 从 Foundry dnd5e 6.0.x 包提取（SRD 5.1，CC-BY-4.0）。

### 5.1 规则数据来源

| 文件 | 内容 |
|------|------|
| `core.json` | 属性修正公式、标准数组、熟练加值表、DC 表、XP 表 |
| `abilities.json` | 六大属性（str/dex/con/int/wis/cha） |
| `skills.json` | 18 项技能及关联属性、中英文别名 |
| `classes.json` | 12 职业：生命骰、豁免熟练、技能选择池 |
| `races.json` | 9 种族：属性加值、速度、语言 |
| `backgrounds.json` | 背景：技能熟练、语言 |

### 5.2 属性修正值（SRD 标准）

```
modifier = floor((score - 10) / 2)
```

示例：敏捷 16 → +3；智力 8 → -1。上限 20（MVP 1 级）。

### 5.3 属性分配（角色创建）

二选一，由 `rule_service.validate_attributes()` 校验：

- **标准数组**：15, 14, 13, 12, 10, 8（`core.json`）
- **27 点购买**：8–15 分，总分 27（`core.json`）

分配后叠加种族 `ability_increases`（如高精灵：敏捷 +2，智力 +1）。

### 5.4 熟练加值

```
level 1–4  → +2
level 5–8  → +3
level 9–12 → +4
...（见 core.json proficiency_bonus_by_level）
```

MVP 固定 1 级，熟练加值 = **+2**。

### 5.5 技能检定（整合后）

```
dice_roll       = random.randint(1, 20)     # 后端生成
ability_mod     = modifier(关联属性)         # 来自 skills.json
skill_bonus     = proficiency_bonus         # 若技能熟练
                  = proficiency_bonus * 2   # 若专精（P1）
                  = 0                       # 未熟练
final_value     = dice_roll + ability_mod + skill_bonus
is_success      = final_value >= dc
```

**示例**：1 级游荡者（敏捷 16，隐匿熟练）潜行，DC 15  
→ d20(11) + 3(敏捷) + 2(熟练) = **16 ≥ 15，成功**

### 5.6 DC 参考（SRD）

| 难度 | DC | 场景示例 |
|------|-----|----------|
| 非常容易 | 5 | 几乎不会失败 |
| 简单 | 10 | 观察明显线索 |
| 中等 | 15 | 悄悄绕过守卫 |
| 困难 | 20 | 欺骗老练 NPC |
| 非常困难 | 25 | 破译古代符文 |
| 几乎不可能 | 30 | 极限挑战 |

AI 给出 `suggested_dc` 后，后端钳制到 `[5, 30]`。

### 5.7 生命值（1 级）

```
max_hp = hit_dice_max + constitution_modifier
```

`hit_dice_max` 来自职业（如 rogue → d8 → 8）。

### 5.8 角色创建规则链

```
race_id → ability_increases
class_id → hit_dice, saving_throws, skill_choices（选 N 项）
background_id → 追加 skill_proficiencies
→ 合并 skills_json → 计算 max_hp、proficiency_bonus
```

### 5.9 豁免检定（P1）

```
total = d20 + ability_mod + (proficiency_bonus if save in saving_throws_json else 0)
```

### 5.10 战斗简化（P2 预留）

```
命中：d20 + ability_mod + proficiency_bonus >= 敌人 AC
伤害：武器骰 + 属性修正
```

### 5.11 rule_service 接口（后端实现参考）

```python
def ability_modifier(score: int) -> int:
    return (score - 10) // 2

def skill_bonus(character, skill_key: str) -> int:
    prof = character.proficiency_bonus
    skill = character.skills_json.get(skill_key, {})
    if skill.get("expertise"):
        return prof * 2
    if skill.get("proficient"):
        return prof
    return 0

def resolve_check(character, skill_key: str, dc: int) -> CheckResult:
    ability = SKILLS[skill_key]["ability"]  # 来自 rules/dnd5e/skills.json
    mod = ability_modifier(getattr(character, ABILITIES[ability]["key"]))
    bonus = skill_bonus(character, skill_key)
    roll = roll_d20()
    total = roll + mod + bonus
    return CheckResult(roll, mod, bonus, total, total >= dc)
```

---

## 6. 数据模型

### 6.1 ER 关系概览

```
users 1──N characters
users 1──N sessions
worlds 1──N sessions
characters 1──N sessions
sessions 1──N messages
sessions 1──N action_checks
sessions 1──N clues
sessions 1──N tasks
sessions 1──1 reports
```

### 6.2 表结构（SQLite 友好 DDL）

```sql
-- 用户
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    nickname      TEXT,
    role          TEXT NOT NULL DEFAULT 'user',  -- user | admin
    avatar_url    TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 世界观
CREATE TABLE worlds (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    type           TEXT NOT NULL,  -- fantasy | mystery | cyberpunk | custom
    description    TEXT,
    opening_prompt TEXT,           -- AI 开局 system 上下文
    rule_style     TEXT DEFAULT 'lite_dnd',
    difficulty     TEXT DEFAULT 'normal',
    cover_url      TEXT,
    created_by     INTEGER REFERENCES users(id),
    is_public      INTEGER DEFAULT 1,
    is_enabled     INTEGER DEFAULT 1,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 角色（D&D 5e 字段整合）
CREATE TABLE characters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    name            TEXT NOT NULL,
    race_id         TEXT,              -- dnd5e: high-elf, human, ...
    class_id        TEXT,              -- dnd5e: rogue, fighter, ...
    background_id   TEXT,              -- dnd5e: acolyte, ...
    motivation      TEXT,
    level           INTEGER DEFAULT 1,
    exp             INTEGER DEFAULT 0,
    hp              INTEGER DEFAULT 10,
    max_hp          INTEGER DEFAULT 10,
    hit_dice        TEXT DEFAULT 'd8',
    proficiency_bonus INTEGER DEFAULT 2,
    strength        INTEGER NOT NULL DEFAULT 10,
    dexterity       INTEGER NOT NULL DEFAULT 10,
    constitution    INTEGER NOT NULL DEFAULT 10,
    intelligence    INTEGER NOT NULL DEFAULT 10,
    wisdom          INTEGER NOT NULL DEFAULT 10,
    charisma        INTEGER NOT NULL DEFAULT 10,
    skills_json     TEXT DEFAULT '{}',       -- {"ste":{"proficient":true},...}
    saving_throws_json TEXT DEFAULT '[]',    -- ["dexterity","intelligence"]
    inventory_json  TEXT DEFAULT '[]',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 跑团会话
CREATE TABLE sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    world_id      INTEGER NOT NULL REFERENCES worlds(id),
    character_id  INTEGER NOT NULL REFERENCES characters(id),
    title         TEXT,
    status        TEXT NOT NULL DEFAULT 'playing',  -- playing | finished | archived
    current_scene TEXT,
    current_task  TEXT,
    summary       TEXT,
    started_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at      DATETIME
);

-- 消息日志
CREATE TABLE messages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL REFERENCES sessions(id),
    sender_type  TEXT NOT NULL,  -- player | ai | npc | system
    sender_name  TEXT,
    content      TEXT NOT NULL,
    message_type TEXT NOT NULL,  -- narration | action | dialogue | dice | clue | task
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 行动判定
CREATE TABLE action_checks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES sessions(id),
    message_id      INTEGER REFERENCES messages(id),
    action_text     TEXT NOT NULL,
    check_type      TEXT,
    skill_key       TEXT,          -- dnd5e 技能键，如 ste
    attribute_used  TEXT,
    dc              INTEGER,
    dice_roll       INTEGER,
    ability_modifier INTEGER,
    skill_bonus     INTEGER DEFAULT 0,
    final_value     INTEGER,
    is_success      INTEGER,     -- 0/1
    result_text     TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 线索
CREATE TABLE clues (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER NOT NULL REFERENCES sessions(id),
    title         TEXT NOT NULL,
    content       TEXT,
    source_scene  TEXT,
    importance    TEXT DEFAULT 'normal',  -- normal | important | key
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 任务
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id),
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT DEFAULT 'todo',  -- todo | doing | done | failed
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 结局报告
CREATE TABLE reports (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         INTEGER NOT NULL UNIQUE REFERENCES sessions(id),
    title              TEXT,
    story_summary      TEXT,
    key_choices_json   TEXT DEFAULT '[]',
    clues_json         TEXT DEFAULT '[]',
    ending_type        TEXT,  -- good | normal | bad | open
    character_growth   TEXT,
    ai_suggestion      TEXT,
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.3 索引建议

```sql
CREATE INDEX idx_sessions_user_status ON sessions(user_id, status);
CREATE INDEX idx_messages_session ON messages(session_id, created_at);
CREATE INDEX idx_action_checks_session ON action_checks(session_id);
```

### 6.4 初始化种子数据

`backend/app/db/init_data.py` 至少插入：
- 1 个 admin 用户（`admin` / 答辩用密码，.env 配置）
- 2 个世界观：`奇幻遗迹`、`古堡悬疑`
- 每个世界观含 `opening_prompt` 与 `description`

---

## 7. API 规范

### 7.1 通用约定

- Base URL：`/api/v1`
- 认证：`Authorization: Bearer <token>`
- Content-Type：`application/json`
- 时间字段：ISO 8601 字符串

### 7.2 统一响应格式

**成功**：

```json
{
  "code": 0,
  "message": "ok",
  "data": { }
}
```

**失败**：

```json
{
  "code": 40001,
  "message": "session is not in playing status",
  "data": null
}
```

### 7.3 错误码表

| code | HTTP | 含义 |
|------|------|------|
| 0 | 200 | 成功 |
| 40101 | 401 | 未登录或 Token 无效 |
| 40301 | 403 | 无权限（如非 admin） |
| 40401 | 404 | 资源不存在 |
| 40901 | 409 | 已有进行中的 session |
| 42201 | 422 | 参数校验失败 |
| 50001 | 500 | 服务器内部错误 |
| 50301 | 503 | AI 服务不可用（可触发兜底叙事） |

### 7.4 接口清单

#### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/register` | 注册 |
| POST | `/auth/login` | 登录，返回 token |
| GET | `/auth/me` | 当前用户信息 |

**POST /auth/login 响应**：

```json
{
  "code": 0,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "user": { "id": 1, "username": "demo", "nickname": "演示用户", "role": "user" }
  }
}
```

#### 世界观

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/worlds` | 列表（仅 `is_enabled=1`） |
| GET | `/worlds/{id}` | 详情 |

#### 规则（D&D 5e）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/rules/dnd5e/summary` | 种族/职业/背景列表（供角色创建页） |
| GET | `/rules/dnd5e/skills` | 18 项技能及关联属性 |

#### 角色

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/characters` | 创建角色（含 D&D 5e 字段） |
| GET | `/characters` | 我的角色列表 |
| GET | `/characters/{id}` | 角色详情 |

**POST /characters 请求**：

```json
{
  "name": "艾琳",
  "race_id": "high-elf",
  "class_id": "rogue",
  "background_id": "acolyte",
  "motivation": "寻找失踪的导师",
  "ability_assignment": "standard_array",
  "base_attributes": {
    "strength": 8,
    "dexterity": 15,
    "constitution": 12,
    "intelligence": 14,
    "wisdom": 13,
    "charisma": 10
  },
  "selected_skills": ["ste", "inv", "prc", "ins"]
}
```

后端处理：应用种族加值 → 合并背景技能熟练 → 校验技能数量 → 计算 `max_hp`、`skills_json`。

#### 会话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/sessions/start` | 开始新局 |
| GET | `/sessions` | 我的历史会话 |
| GET | `/sessions/{id}` | 会话详情（含最近消息） |
| GET | `/sessions/{id}/messages` | 分页消息列表 |
| POST | `/sessions/{id}/end` | 结束本局（status → finished） |

**POST /sessions/start 请求**：

```json
{
  "world_id": 1,
  "character_id": 3
}
```

**POST /sessions/start 响应（节选）**：

```json
{
  "code": 0,
  "data": {
    "session": { "id": 12, "status": "playing", "title": "雾中的古堡", "current_task": "调查失踪学者" },
    "opening": {
      "scene_title": "雾中的古堡",
      "narration": "夜色降临，你来到一座被浓雾包围的古堡前……",
      "main_task": "调查古堡中失踪的学者",
      "npcs": [{ "name": "老管家", "description": "神情紧张" }],
      "initial_clues": []
    },
    "messages": [ ]
  }
}
```

#### 行动（核心）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/sessions/{id}/action` | 提交玩家行动 |

**请求**：

```json
{
  "action_text": "我想偷偷绕过守卫。"
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "player_message": { "id": 101, "content": "我想偷偷绕过守卫。", "message_type": "action" },
    "check": {
      "check_type": "隐匿",
      "skill_key": "ste",
      "attribute_used": "dexterity",
      "dc": 15,
      "dice_roll": 11,
      "ability_modifier": 3,
      "skill_bonus": 2,
      "final_value": 16,
      "is_success": true,
      "result_text": "d20(11) + 敏捷(+3) + 熟练(+2) = 16 ≥ DC 15，成功"
    },
    "story": {
      "narration": "你压低脚步，从阴影中穿过。守卫似乎听到了什么，但他只是回头看了一眼，并没有发现你。",
      "new_clues": [],
      "task_updates": [],
      "status_changes": [],
      "next_options": ["继续跟踪守卫", "调查走廊尽头的房间", "返回大厅"]
    }
  }
}
```

#### 报告

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/sessions/{id}/report/generate` | 生成报告（幂等：已存在则返回已有） |
| GET | `/sessions/{id}/report` | 获取报告 |

#### 管理端（P1，需 admin 角色）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/stats` | 总用户数、会话数、完成率、判定成功率 |
| GET | `/admin/sessions` | 全部会话列表 |
| GET/POST/PUT/DELETE | `/admin/worlds` | 世界观 CRUD |

---

## 8. 核心业务流程

### 8.1 开局流程

```
前端：选 world + character
  → POST /sessions/start
后端：校验无其他 playing session
  → 创建 session(status=playing)
  → 调用 ai_service.generate_opening(world, character)
  → 写入 messages(narration)、tasks(main_task)、clues(initial)
  → 返回 opening + session
前端：router.push(/sessions/:id/play)
```

### 8.2 行动流程（时序）

```
Frontend          API              ai_service        dice_service       DB
   │ POST /action   │                    │                  │              │
   │───────────────►│ load session       │                  │              │
   │                │──────────────────────────────────────────────────────►│
   │                │ parse_action       │                  │              │
   │                │───────────────────►│                  │              │
   │                │◄───────────────────│ JSON: type, attr, dc             │
   │                │ roll & judge       │                  │              │
   │                │─────────────────────────────────────►│              │
   │                │◄─────────────────────────────────────│              │
   │                │ narrate(check)     │                  │              │
   │                │───────────────────►│                  │              │
   │                │ persist all        │                  │              │
   │                │──────────────────────────────────────────────────────►│
   │◄───────────────│ response           │                  │              │
```

### 8.3 结束流程

```
用户点击「结束本局」
  → POST /sessions/{id}/end        # status = finished
  → POST /sessions/{id}/report/generate
  → ai_service.generate_report(session_logs)
  → 写入 reports
  → 前端跳转 /sessions/:id/report
```

### 8.4 是否使用 WebSocket？

**MVP：否。** 单人跑团 HTTP 足够。打字机效果由前端对 `narration` 逐字渲染即可。  
**二期**：多人同房、实时掷骰展示可考虑 WebSocket。

---

## 9. AI 模块规范

### 9.1 设计原则

1. **所有 AI 输出必须为 JSON**，后端 Pydantic 校验后再落库  
2. **骰子由后端生成**，Prompt 中明确禁止 AI 输出 random 值  
3. **上下文截断**：传给 AI 的历史消息保留最近 N 条 + 会话摘要（防 token 爆炸）  
4. **失败兜底**：AI 超时或 JSON 解析失败时，使用 `ai_service.fallback_narration()`

### 9.2 Prompt 文件组织

```
backend/app/prompts/
├── opening.txt       # 开局生成
├── action_parse.txt  # 行动理解
├── narrate.txt       # 判定后叙事
└── report.txt        # 本局总结
```

### 9.3 行动理解 — 输出 Schema

```json
{
  "action_type": "stealth",
  "skill_key": "ste",
  "check_type": "隐匿",
  "attribute_used": "dexterity",
  "suggested_dc": 15,
  "needs_check": true,
  "reason": "玩家试图绕过守卫，属于敏捷相关的隐匿动作"
}
```

- `skill_key` 必须为 `skills.json` 中的键（如 `ste`、`inv`）
- `needs_check: false` 时跳过掷骰（纯对话、查看已有线索等）
- `attribute_used` 枚举：`strength | dexterity | constitution | intelligence | wisdom | charisma`

### 9.4 剧情推进 — 输出 Schema

```json
{
  "narration": "你压低脚步，从阴影中穿过……",
  "new_clues": [
    { "title": "脚印", "content": "通往地下室", "importance": "important" }
  ],
  "task_updates": [
    { "title": "调查失踪学者", "status": "doing" }
  ],
  "status_changes": [
    { "field": "hp", "delta": -2, "reason": "踩中陷阱" }
  ],
  "next_options": ["继续跟踪", "调查房间", "返回大厅"]
}
```

### 9.5 本局总结 — 输出 Schema

```json
{
  "title": "古堡阴影下的低语",
  "story_summary": "本局中，玩家进入古堡并发现……",
  "key_choices": ["成功绕过守卫", "发现地下室入口"],
  "ending_type": "open",
  "character_growth": "获得 50 点经验，洞察 +1",
  "next_suggestion": "下一局可探索封印房间"
}
```

### 9.6 AI 配置项（.env）

| 变量 | 说明 |
|------|------|
| `LLM_API_BASE` | API 基址 |
| `LLM_API_KEY` | 密钥 |
| `LLM_MODEL` | 模型名 |
| `LLM_TIMEOUT` | 超时秒数，建议 30 |
| `LLM_MAX_TOKENS` | 单次最大 token |

---

## 10. 前端实现清单

### 10.1 路由表

| 路径 | 组件 | 优先级 |
|------|------|--------|
| `/login` | LoginView | P0 |
| `/register` | RegisterView | P0 |
| `/home` | HomeView | P0 |
| `/worlds` | WorldSelectView | P0 |
| `/character/create` | CharacterCreateView | P0 |
| `/sessions/:id/play` | GameSessionView | P0 |
| `/sessions/:id/report` | ReportView | P0 |
| `/archive` | ArchiveView | P1 |
| `/admin` | AdminDashboardView | P1 |

### 10.2 跑团主界面布局

```
┌──────────────┬────────────────────────────┬──────────────┐
│ 角色状态栏   │      剧情对话区             │  功能 Tab    │
│ - 名/职业    │  StoryMessage 列表          │  骰子判定    │
│ - HP/等级    │  PlayerActionInput          │  线索记录    │
│ - 属性雷达   │  快捷：调查/对话/移动/战斗   │  任务状态    │
│              │                             │  历史日志    │
└──────────────┴────────────────────────────┴──────────────┘
```

### 10.3 关键组件

| 组件 | 职责 |
|------|------|
| `AttributeRadar.vue` | ECharts 雷达图，绑定六大属性 |
| `StoryMessage.vue` | 区分 ai / player / system / dice 样式 |
| `DiceResultCard.vue` | 展示 d20 + 修正 + DC + 成功/失败 |
| `PlayerActionInput.vue` | 自由输入 + 快捷按钮 + loading |
| `ResultChart.vue` | 报告页统计图 |

### 10.4 前端状态（Pinia `sessionStore`）

```typescript
interface SessionState {
  currentSession: Session | null
  messages: Message[]
  clues: Clue[]
  tasks: Task[]
  isSubmitting: boolean   // 行动提交中，防重复点击
}
```

### 10.5 交互要点

- 提交行动时禁用输入框，显示 loading，完成后滚动到底部  
- AI 叙事可选打字机效果（`setInterval` 逐字，非必须）  
- 骰子结果用独立卡片样式，与旁白消息区分  
- 401 响应统一跳转登录页  

---

## 11. 后端实现清单

### 11.1 Service 职责

| Service | 职责 |
|---------|------|
| `auth_service` | 注册、登录、JWT、密码哈希 |
| `world_service` | 世界观 CRUD、种子数据 |
| `character_service` | 创建角色、属性校验 |
| `session_service` | 会话生命周期、消息查询 |
| `dice_service` | `roll_d20()`、`compute_check()` |
| `rule_service` | 属性修正、DC 钳制、属性点校验 |
| `ai_service` | 调 LLM、解析 JSON、兜底 |
| `report_service` | 汇总日志、生成报告 |

### 11.2 `action_service.handle_action()` 伪代码

```python
def handle_action(session_id, user_id, action_text):
    session = get_playing_session(session_id, user_id)

    context = build_context(session)  # world, character, recent messages, clues
    parsed = ai_service.parse_action(context, action_text)

    if parsed.needs_check:
        dc = rule_service.clamp_dc(parsed.suggested_dc)
        check = dice_service.roll_check(
            attribute=getattr(session.character, parsed.attribute_used),
            dc=dc,
            check_type=parsed.check_type,
            action_text=action_text,
        )
    else:
        check = None

    story = ai_service.narrate(context, action_text, check)
    return persist_and_build_response(session, action_text, check, story)
```

### 11.3 事务与持久化顺序

同一事务内依次写入：
1. `messages` — 玩家行动  
2. `action_checks` — 若有判定  
3. `messages` — 系统骰子消息  
4. `messages` — AI 旁白  
5. `clues` / `tasks` — 若有更新  
6. `sessions.current_scene` / `current_task` — 若 AI 返回场景变化  

---

## 12. 环境配置与本地启动

### 12.1 环境变量模板

| 文件 | 说明 |
|------|------|
| `.env.example` | 后端完整模板（数据库、JWT、LLM、CORS、种子账号） |
| `frontend/.env.example` | 前端 Vite 变量（`VITE_API_BASE_URL` 等） |
| `backend/.env.example` | 从 `backend/` 目录启动时的备用模板 |

组内成员首次配置：

```bash
./scripts/setup-env.sh          # macOS / Linux
# 或 Windows: .\scripts\setup-env.ps1
```

**必填项**：`LLM_API_KEY`、`SECRET_KEY`（生产环境）。各 LLM 提供商预设见 `.env.example` 注释。

```env
# 核心 excerpt — 完整项见 .env.example
DATABASE_URL=sqlite:///./data/storyforge.db
SECRET_KEY=change-me-in-production
JWT_EXPIRE_MINUTES=1440

LLM_PROVIDER=deepseek
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=                        # 必填
LLM_MODEL=deepseek-chat
LLM_TIMEOUT=60

FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

前端 `frontend/.env`：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_HTTP_TIMEOUT=90000
```

### 12.2 本地启动命令（目标态）

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### 12.3 联调地址

- 前端：http://localhost:5173  
- 后端：http://localhost:8000  
- API 文档：http://localhost:8000/docs  

---

## 13. 五天开发里程碑

| 天 | 后端 | 前端 | AI |
|----|------|------|-----|
| **D1** | 项目骨架、DB 模型、auth API、种子数据 | 项目骨架、登录注册、路由 | Prompt 草稿 |
| **D2** | worlds / characters / sessions/start | 世界观选择、角色创建、雷达图 | opening + parse Prompt 联调 |
| **D3** | action 全流程、dice_service | 跑团主界面三栏、消息流 | narrate Prompt 联调 |
| **D4** | report 生成、admin stats | 报告页、图表、历史档案 | report Prompt + JSON 兜底 |
| **D5** | Bug 修复、CORS、部署脚本 | UI 打磨、答辩演示排练 | 边界 case 测试 |

### 13.1 小组分工（与里程碑对齐）

| 角色 | 交付物 |
|------|--------|
| **前端** | 8 个页面 + 三栏跑团界面 + ECharts |
| **后端** | 全部 P0 API + 事务持久化 + Swagger 文档 |
| **AI** | 4 套 Prompt + JSON Schema 校验 + 兜底文案 |
| **数据/可视化** | DDL、种子数据、管理端统计、答辩图表 |

---

## 14. 测试与答辩演示脚本

### 14.1 手动测试检查表

- [ ] 注册新用户并登录  
- [ ] 创建角色，属性总和符合规则  
- [ ] 开始新局，出现开局旁白与主任务  
- [ ] 提交行动，骰子结果每次不同（验证非 AI 生成）  
- [ ] 刷新 play 页，历史消息仍在  
- [ ] 结束本局，报告页数据完整  
- [ ] 管理端（P1）能看到会话统计  

### 14.2 答辩演示脚本（约 5 分钟）

```
1. 登录 StoryForge
2. 选择「古堡悬疑」世界观
3. 创建角色「艾琳」，职业调查员，展示雷达图
4. 系统生成开局剧情
5. 输入：「我想偷偷绕过守卫。」
6. 展示 d20 判定卡片（DC、修正、成功）
7. AI 推进剧情，展示 1 条线索（若有）
8. 再行动 2 轮
9. 结束本局 → 战报页（摘要 + 图表）
10. 管理后台：世界观热度、判定成功率
```

**演示要点**：强调「AI 不替系统掷骰，规则与叙事分工明确」。

---

## 15. 附录

### 15.1 行动判定示例

**玩家输入**：我想偷偷绕过守卫。

**系统判定**：
- 检定类型：敏捷 / 潜行  
- DC：14  
- d20：11 + 敏捷修正 +3 = **14** → **成功**

**AI 输出**：你压低脚步，从阴影中穿过。守卫似乎听到了什么，但他只是回头看了一眼，并没有发现你。

### 15.2 参考开源项目

- SillyTavern — AI 角色扮演 UI 参考  
- KoboldAI — 本地/远程 LLM 接入参考  
- Avrae — 跑团判定逻辑参考  
- FoundryVTT — 会话与模组组织参考  

### 15.3 文档修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-07 | 从产品设计稿重构为实现规格书 |

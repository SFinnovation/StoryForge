# 架构设计

## 2026-07-08 架构补充

- API 层新增 `backend/app/api/v1/admin.py`，统一提供 `/api/v1/admin` 管理员后台接口。
- 权限层新增 `get_current_admin_user()`，管理员接口必须携带管理员 Bearer token；普通用户被封禁后不能登录，也不能继续使用带 token 的普通接口。
- 数据库扩展后台管理表：`world_modules` 管理世界观下模组，`admin_operation_logs` 记录管理员操作。
- `users` 表补充 `email` 与 `status`，账号状态支持 `active` / `banned`。
- 前端仍无管理员页面；当前仅后端与数据库已准备好，等待前端管理后台对接。

> 本文档描述当前仓库的实际架构与模块边界。更完整的目标规格见 [implementation-spec.md](implementation-spec.md)，逐模块检查见 [module-audit.md](module-audit.md)。

## 概述

StoryForge 采用前后端分离的 monorepo 结构。后端负责规则判定、AI 编排、数据持久化与 API；前端负责跑团体验界面；D&D 5e 规则以静态 JSON 存放在 `rules/dnd5e/`，不写入业务库。

```text
frontend (Vue 3 + Vite)
        |
        | HTTP / JSON
        v
backend.app.api.v1 (FastAPI Router)
        |
        v
services / ai orchestrator / repositories
        |
        v
SQLAlchemy ORM -> SQLite

rules/dnd5e/*.json -> rule_service / character creation / action checks
```

## 分层职责

| 层级 | 路径 | 职责 |
|------|------|------|
| 前端界面 | `frontend/src/` | 大厅、世界观、档案、角色创建等 Vue 页面原型 |
| API 层 | `backend/app/api/v1/` | FastAPI 路由，统一返回 `ApiResponse` |
| 业务服务 | `backend/app/services/` | 会话生命周期、行动编排、规则判定、上下文构建、报告、导出 |
| AI 模块 | `backend/app/ai/` | 五 Agent、Prompt、LLM Client、JSON Schema、Revision Loop |
| 仓储层 | `backend/app/repositories/` | Message、Fact、NPC、ActionCheck、Task、Report、AIReview 等读写封装 |
| 数据模型 | `backend/app/models/` | SQLAlchemy ORM，覆盖 12 张核心表 |
| Schema | `backend/app/schemas/` 与 `backend/app/ai/schemas/` | API 请求响应和 Agent 输入输出校验 |
| 规则数据 | `rules/dnd5e/` | D&D 5e SRD 静态规则 |
| 验证脚本 | `backend/scripts/` | API、AI、DB、仓储和性能验证脚本 |

## 核心业务闭环

```text
选择世界观
  -> 创建角色
  -> POST /sessions/start
  -> OpeningAgent 生成开局
  -> 玩家提交行动
  -> ActionParserAgent 解析技能与 DC
  -> rule_service 后端掷骰并计算结果
  -> ContextBuilder 裁剪上下文
  -> NarrativeAgent 生成剧情
  -> CriticAgent 审核
  -> RevisionLoop 修正或 fallback
  -> StateCommitter 按事务写入消息、判定、线索、任务、Fact、AI Review
  -> SummaryAgent 生成本局报告
```

## 核心模块

### 1. 会话与行动

- 路由：`backend/app/api/v1/sessions.py`
- 服务：`session_service.py`、`action_service.py`
- 状态：`playing -> finished -> archived`
- 约束：只有 `playing` 会话允许继续提交行动；MVP 中同一用户同时只允许一个 `playing` 会话。

### 2. 规则引擎

- 规则文件：`rules/dnd5e/core.json`、`skills.json`、`classes.json`、`races.json`、`backgrounds.json`
- 服务：`rule_service.py`
- 硬约束：掷骰、属性修正、熟练加值和成败判定由后端生成，AI 只负责理解行动和叙事。

### 3. AI 编排

- Agent：Opening、ActionParser、Narrative、Critic、Summary
- 编排入口：`backend/app/ai/orchestrator.py` 与 `backend/app/services/ai_service.py`
- 兜底：未配置 `LLM_API_KEY` 时走 `fallbacks.py`，便于本地闭环联调。

### 4. 数据持久化

基础表：

- `users`
- `worlds`
- `characters`
- `game_sessions`
- `messages`
- `action_checks`
- `clues`
- `tasks`
- `reports`

AI 扩展表：

- `facts`
- `npc_profiles`
- `ai_reviews`

DDL 位于 `backend/app/db/schema.sql`，ORM 位于 `backend/app/models/models.py`。根目录 `数据库存储结构设计.sql` 是数据库设计交付文档，当前后端以 `backend/app/db/schema.sql` 和 ORM 为运行依据。

### 5. 传统故事创作模块

仓库仍保留故事、章节、设定库和导出模块：

- `stories.py` / `story_service.py`
- `chapters.py` / `chapter_service.py`
- `worldbuilding.py` / `worldbuilding_service.py`
- `export.py` / `ExportService`

这些模块提供基础 CRUD 和 Markdown 导出，PDF 导出仍是待实现项。

### 6. 内容知识引擎（Content Knowledge）— 📋 方案待实施

规则书（PHB）与冒险模组 docx 的导入分两层：

- **语义层（已实现）**：`RulebookExtractorAgent` / `ModuleExtractorAgent` → `rulebook_packs` / `adventure_modules`
- **知识引擎层（规划）**：接入 [Auditable Knowledge Packs](akp-integration-plan.md)，提供确定性、强出处、可复现的非向量检索，作为 Extractor Agent 的底层证据源与 Critic 的规则校验依据

集成方案见 [akp-integration-plan.md](akp-integration-plan.md)（三种模式、P0–P2 路线图、可开关回退）。

## API 原则

- 路由统一挂载在 `/api/v1`
- 成功响应使用 `{"code": 0, "message": "ok", "data": ...}`
- 业务错误通过 `StoryForgeError` 转换为统一错误响应
- 当前认证仍为演示占位：`get_current_user_id()` 固定返回 `1`

## 当前技术债

- 前端尚未接入真实 API、Vue Router、Pinia 与统一请求层。
- 前端构建已通过，但 `/src/assets/auth-bg.png` 当前未解析，运行时需要补资产或调整路径。
- 认证当前为 MVP bearer token，生产前仍需标准 JWT/RBAC 与密码安全策略。
- `POST /characters` 已接入 D&D 5e MVP 规则链，27 点购与选择型种族/技能分支仍待完善。
- `ExportService.export_pdf()` 仍返回 501。
- `.env.example` 与运行默认值需持续保持一致，避免不同启动目录下 SQLite 路径混乱。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-08 | 新增内容知识引擎章节，链接 AKP 集成方案 |
| 2026-07-08 | 清理冲突标记，按当前仓库结构重写架构说明 |
| 2026-07-07 | 初始文档骨架 |

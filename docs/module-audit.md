# 模块检查报告

## 2026-07-08 进度补充

| 模块 | 当前状态 | 结论 |
|------|----------|------|
| 前端 API 联调 | 已推进 | 登录/注册、世界观、角色、会话、档案读取等主流程已接入现有后端接口 |
| 前端导航与登录页 | 已调整 | 顶栏文字入口已移除，登录注册页移除“继续上次冒险”，并导出静态 HTML 供外部编辑 |
| 管理员后台后端 | 已实现第一版 | 新增 `/api/v1/admin` 接口组，覆盖世界观/模组、会话记录、用户、操作日志 |
| 管理员后台前端 | 待接入 | 当前只完成数据库与后端逻辑，前端管理页面等待后续对接 |
| 数据库 | 已扩展 | 新增 `world_modules`、`admin_operation_logs`，`users` 补充 `email/status` |

本轮新增验证：

- `.venv\Scripts\python.exe -m backend.scripts.test_admin_api`
- `.venv\Scripts\python.exe -m backend.scripts.test_frontend_contract`
- `.venv\Scripts\python.exe -m compileall backend`

> 检查日期：2026-07-08  
> 范围：按当前文件结构核对文档要求、实现状态与可运行性。本文不替代实现规格书，而是给团队一个“现在仓库到底到哪了”的快照。

## 检查结论

| 模块 | 状态 | 结论 |
|------|------|------|
| 文档入口 | 已修复 | README、架构、快速开始已按当前结构重写，冲突标记已清理 |
| 环境模板 | 已修复 | `.env.example` 去除冲突标记，并与当前后端默认值对齐 |
| Git 忽略规则 | 已修复 | `.gitignore` 去除冲突标记，保留数据库、data、uploads、node_modules 忽略 |
| 后端主闭环 | 基本完成 | auth、rules、worlds、characters、sessions、action、report 与 P1 调试接口均有实现 |
| AI 模块 | 基本完成 | 五 Agent、Prompt、Schema、RevisionLoop、fallback 已存在 |
| 数据库/仓储 | 基本完成 | 12 张表、ORM、仓储层与验证脚本齐全 |
| D&D 5e 规则 | MVP 完成 | JSON 查询、标准数组、种族加值、职业 HP/豁免、技能熟练写入已接入 |
| 前端 | 原型阶段 | 页面原型已存在，未接真实 API、Router、Pinia；依赖已可安装并构建 |
| 认证/权限 | MVP 完成 | 注册、登录、`/auth/me` 与 Bearer token 可用；生产级 JWT/RBAC 待强化 |
| 导出 | 部分完成 | Markdown 导出可用，PDF 待实现 |

## 本次同步修复

- 清理 `README.md`、`docs/architecture.md`、`.env.example`、`.gitignore` 中遗留的冲突标记。
- 将 `frontend/package.json` 依赖版本对齐 `package-lock.json`，使 `npm ci` 可执行。
- 修复 `session_service` 中 `world.is_active` 与 ORM 字段不一致的问题，统一使用 `is_enabled`。
- 修复 `game_sessions.started_at/ended_at` 与 `reports.created_at` 写入字符串导致 SQLite `DateTime` 报错的问题。
- 让 `MessageDTO.created_at` 兼容 ORM 返回的 `datetime`。
- 清理 `NpcProfile.alertness` 重复字段定义。
- 将 `verify_implementation_spec.py`、`test_action_api.py`、`verify_ai_db_interaction.py`、`verify_repositories.py` 调整为可独立运行的验证脚本。
- 新增 auth、rules API、会话详情 API 与前端契约测试脚本 `test_frontend_contract.py`。
- 角色创建支持文档中的 D&D 5e payload，并写入种族属性加值、职业 HP、豁免与技能熟练。

## 文件结构映射

```text
StoryForge/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI 路由
│   │   ├── ai/              # Agent、Prompt、LLM Client、AI Schema
│   │   ├── core/            # 配置与异常
│   │   ├── db/              # 数据库连接、DDL、初始化
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── repositories/    # 仓储封装
│   │   ├── schemas/         # API Schema
│   │   └── services/        # 业务服务与编排
│   ├── scripts/             # 后端验证脚本
│   └── requirements.txt
├── frontend/
│   ├── src/                 # Vue 页面原型
│   ├── package.json
│   └── package-lock.json
├── rules/dnd5e/             # D&D 5e SRD JSON
├── scripts/                 # 项目级脚本
├── docs/                    # 产品、实现、架构与检查文档
└── backend.md               # 后端接口契约快照
```

## P0 需求对照

| P0 需求 | 文档来源 | 当前实现 | 结论 |
|---------|----------|----------|------|
| 用户注册/登录 | implementation-spec §3.1 | `/auth/register`、`/auth/login`、`/auth/me` 可用 | 完成 |
| 世界观列表与选择 | implementation-spec §3.1 | `GET /worlds` 后端可用，前端静态 | 部分完成 |
| D&D 5e 角色创建 | implementation-spec §5 / §7.4 | 标准数组、种族加值、职业 HP/豁免、技能熟练 MVP 已接入 | 完成 |
| 开始新局 + AI 开局 | implementation-spec §8.1 | `POST /sessions/start` 可用 | 完成 |
| 玩家行动 + d20 判定 | implementation-spec §8.2 | `POST /sessions/{id}/action` 可用 | 完成 |
| 消息与判定持久化 | implementation-spec §6 / §11 | `messages`、`action_checks` 写入路径存在 | 完成 |
| 本局总结报告 | implementation-spec §8.3 | SummaryAgent + `reports` 可用 | 完成 |
| 跑团主界面三栏布局 | implementation-spec §10.2 | 前端尚无真实 GameSession 页面 | 待补 |

## 后端模块检查

| 子模块 | 文件 | 检查结果 |
|--------|------|----------|
| API 聚合 | `backend/app/api/v1/router.py` | 已挂载 auth、rules、sessions、worlds、characters、stories、chapters、worldbuilding、export |
| 会话 API | `backend/app/api/v1/sessions.py` | 覆盖开局、列表、消息、行动、结束、报告、meta、facts、ai-reviews |
| 认证 API | `backend/app/api/v1/auth.py` | 覆盖注册、登录、当前用户 |
| 规则 API | `backend/app/api/v1/rules.py` | 覆盖 D&D 5e summary 与 skills |
| 世界观 API | `backend/app/api/v1/worlds.py` | 列表与详情可用 |
| 角色 API | `backend/app/api/v1/characters.py` | 创建/列表/详情可用，支持旧 payload 与 D&D 5e payload |
| 故事/章节/设定 | `stories.py`、`chapters.py`、`worldbuilding.py` | CRUD 保留，可作为通用创作模块 |
| 导出 | `export.py`、`services/export.py` | Markdown 可用，PDF 待实现 |
| 配置/异常 | `core/config.py`、`core/exceptions.py` | 基础配置和统一业务异常可用 |
| 数据库 | `db/database.py`、`db/init_db.py` | SQLite 连接、建表、demo 数据入口可用 |
| ORM | `models/models.py` | 12 张表齐全，已清理 `NpcProfile.alertness` 重复字段定义 |
| 仓储层 | `repositories/*.py` | 覆盖 Message、Fact、NPC、ActionCheck、Task、Report、AIReview、Session |
| 行动编排 | `services/action_service.py` | 已串起 ActionParser、Rule、Narrative、Critic、Committer |
| 状态提交 | `services/state_committer.py` | 有事务、校验、写入顺序与非法输出拦截 |

## AI 模块检查

| 子模块 | 文件 | 检查结果 |
|--------|------|----------|
| Agent 门面 | `backend/app/ai/orchestrator.py` | 统一封装 Opening、Parse、Narrative、Summary |
| LLM Client | `backend/app/ai/services/llm_client.py` | OpenAI 兼容接口，Key 为空时 disabled |
| Prompt | `backend/app/ai/prompts/*.txt` | action、narrative、critic、opening、report 均存在 |
| JSON Schema | `backend/app/ai/schemas/*.py`、`*.schema.json` | Agent 输入输出模型存在 |
| fallback | `backend/app/ai/services/fallbacks.py` | 无 Key 可本地演示 |
| Critic/Revision | `critic_agent.py`、`revision_loop.py` | 审核与最多 2 次修正路径存在 |

## 规则与数据库检查

| 项 | 文件 | 结果 |
|----|------|------|
| D&D 核心规则 | `rules/dnd5e/core.json` | JSON 解析通过 |
| 技能规则 | `rules/dnd5e/skills.json` | JSON 解析通过，18 项技能和别名存在 |
| 种族/职业/背景 | `rules/dnd5e/races.json`、`classes.json`、`backgrounds.json` | 已用于角色创建 MVP 派生属性、HP、豁免与熟练技能 |
| DDL | `backend/app/db/schema.sql` | 与 ORM 目标一致，包含 AI 扩展表 |
| 种子 SQL | `backend/app/db/seed.sql` | 有管理员与世界观种子，但运行时主要通过 `init_db.py`/`world_seed.py` |

## 前端模块检查

| 子模块 | 文件 | 检查结果 |
|--------|------|----------|
| App 入口 | `frontend/src/App.vue`、`main.js` | 使用本地 `currentPage` 切换页面，无 Router |
| 大厅 | `HomePage.vue` | 静态大厅、创建房间弹窗、快速加入原型 |
| 世界观 | `ScriptPage.vue` | 静态世界观与模组列表，进入角色页 |
| 角色创建 | `RolePage.vue` | COC/DND 本地属性分配原型，未提交到后端 |
| 档案 | `ArchivePage.vue` | 静态历史档案原型 |
| 登录注册 | `LoginRegister.vue` | 页面存在，但未挂入 `App.vue`，未接 API |
| 样式 | `style.css` 与 SFC scoped styles | 可用；部分页面引用 `/src/assets/auth-bg.png`，仓库当前未见该资产 |
| 构建依赖 | `package.json` / `package-lock.json` | 已将 `package.json` 依赖版本对齐 lockfile，`npm ci` 可执行 |

## 本次验证记录

| 命令 | 结果 |
|------|------|
| `.venv\Scripts\python.exe -m compileall -q backend/app backend/scripts scripts` | 通过 |
| `.venv\Scripts\python.exe -m json.tool rules/dnd5e/*.json` | 通过 |
| `.venv\Scripts\python.exe -m backend.scripts.verify_implementation_spec` | 通过 |
| `.venv\Scripts\python.exe -m backend.scripts.test_action_api` | 通过 |
| `.venv\Scripts\python.exe -m backend.scripts.test_ai_module` | 通过 |
| `.venv\Scripts\python.exe -m backend.scripts.test_frontend_contract` | 通过 |
| `.venv\Scripts\python.exe -m backend.scripts.verify_ai_db_interaction` | 通过 |
| `.venv\Scripts\python.exe -m backend.scripts.verify_repositories` | 通过 |
| `.venv\Scripts\python.exe -m backend.scripts.bench_ai_module` | 通过 |
| `npm.cmd ci --cache .npm-cache --no-audit --no-fund` | 通过 |
| `npm.cmd run build` | 通过；Vite 提醒 `/src/assets/auth-bg.png` 未解析，将在运行时保留原路径 |

## 优先级建议

1. 前端建立请求层与状态层：建议补 Router、Pinia 或轻量 store、API client，再接 auth、rules、worlds、characters、sessions。
2. 强化认证：当前为 MVP bearer token，生产前建议接标准 JWT、密码策略、刷新 token 与 RBAC。
3. 完善 D&D 角色创建：补 27 点购、半精灵/半身人等选择型种族加值与技能选择分支。
4. 修前端资产引用：补 `/src/assets/auth-bg.png` 或改为已有资源路径，消除构建时运行时路径提醒。
5. 清理小代码债：PDF 导出 TODO、管理端 `/admin` 仍待补。
6. 将验证脚本纳入 CI：至少运行 Python compile、前端契约脚本、后端闭环脚本和前端 build。

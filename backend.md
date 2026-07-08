# 后端开发进度与接口契约

## 2026-07-08 管理员后台补充

后端已新增管理员后台数据库与接口逻辑，详见 [docs/admin-backend.md](docs/admin-backend.md)。

新增数据结构：

- `users.email`、`users.status`
- `world_modules`
- `admin_operation_logs`

新增接口前缀：

- `/api/v1/admin/summary`
- `/api/v1/admin/worlds`
- `/api/v1/admin/worlds/{world_id}/modules`
- `/api/v1/admin/modules/{module_id}`
- `/api/v1/admin/sessions`
- `/api/v1/admin/sessions/{session_id}`
- `/api/v1/admin/sessions/{session_id}/dissolve`
- `/api/v1/admin/users`
- `/api/v1/admin/users/{user_id}/reset-password`
- `/api/v1/admin/users/{user_id}/ban`
- `/api/v1/admin/users/{user_id}/unban`
- `/api/v1/admin/operation-logs`

本轮验证：

```powershell
.venv\Scripts\python.exe -m backend.scripts.test_admin_api
.venv\Scripts\python.exe -m backend.scripts.test_frontend_contract
.venv\Scripts\python.exe -m compileall backend
```

> 本文档同步当前后端真实状态。完整目标规格见 [docs/implementation-spec.md](docs/implementation-spec.md)，逐模块检查见 [docs/module-audit.md](docs/module-audit.md)。

## 当前结论

后端已经从第一阶段 mock 调度中心，推进到可运行的 MVP 主闭环：

```text
POST /sessions/start
  -> OpeningAgent
  -> messages/tasks/clues/facts/npc_profiles

POST /sessions/{id}/action
  -> ActionParserAgent
  -> rule_service 后端 d20 判定
  -> NarrativeAgent
  -> CriticAgent + RevisionLoop
  -> messages/action_checks/clues/tasks/facts/ai_reviews

POST /sessions/{id}/report/generate
  -> SummaryAgent
  -> reports
```

## 已实现

### 1. FastAPI 工程骨架

- 入口：`backend/app/main.py`
- 路由聚合：`backend/app/api/v1/router.py`
- 配置：`backend/app/core/config.py`
- 统一业务异常：`StoryForgeError`
- 健康检查：`GET /health`

### 2. 数据库与 ORM

- 运行时 ORM：`backend/app/models/models.py`
- DDL：`backend/app/db/schema.sql`
- 初始化：`backend/app/db/init_db.py`
- 表结构：`users`、`worlds`、`characters`、`game_sessions`、`messages`、`action_checks`、`clues`、`tasks`、`reports`、`facts`、`npc_profiles`、`ai_reviews`

### 3. 认证、规则与跑团主闭环

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/rules/dnd5e/summary`
- `GET /api/v1/rules/dnd5e/skills`

- `POST /api/v1/sessions/start`
- `GET /api/v1/sessions/{session_id}`
- `POST /api/v1/sessions/{session_id}/action`
- `POST /api/v1/sessions/{session_id}/end`
- `POST /api/v1/sessions/{session_id}/report/generate`
- `GET /api/v1/sessions/{session_id}/messages`
- `GET /api/v1/sessions/{session_id}/meta`
- `GET /api/v1/sessions/{session_id}/facts`
- `GET /api/v1/sessions/{session_id}/ai-reviews`

### 4. 角色与世界观接口

- `GET /api/v1/worlds`
- `GET /api/v1/worlds/{world_id}`
- `POST /api/v1/characters/`
- `GET /api/v1/characters`
- `GET /api/v1/characters/{character_id}`

角色接口兼容基础字段写入，并支持文档中的 D&D 5e payload：标准数组校验、种族属性加值、职业 HP/豁免、背景/职业技能熟练写入。

### 5. 传统故事创作接口

- `stories`
- `chapters`
- `worldbuilding`
- `export`

这些接口保留为通用故事创作能力。Markdown 导出可用，PDF 导出仍返回 501。

## 当前占位与限制

| 项 | 当前状态 | 下一步 |
|----|----------|--------|
| 认证 | MVP bearer token 可用，无 token 保留 demo 回退 | 生产前接标准 JWT/RBAC 与刷新机制 |
| 角色创建 | D&D 5e MVP 规则链可用 | 补 27 点购、选择型种族加值和复杂技能选择 |
| CORS | 已挂载 `CORSMiddleware` | 部署时收紧 `CORS_ORIGINS` |
| 前端联调 | API 已有，前端仍是静态原型 | 增加请求层、状态管理与真实页面数据 |
| PDF 导出 | `ExportService.export_pdf()` 未实现 | 选型并补 PDF 导出 |
| 管理端 | 文档列为 P1 | 增加 `/admin` 路由与权限 |

## 验证方式

安装依赖后从仓库根目录运行：

```bash
python -m backend.scripts.verify_implementation_spec
python -m backend.scripts.verify_ai_db_interaction
python -m backend.scripts.test_action_api
python -m backend.scripts.test_frontend_contract
python -m backend.scripts.test_ai_module
python -m backend.scripts.bench_ai_module
```

无需第三方依赖的基础静态检查：

```bash
python -m compileall -q backend/app backend/scripts scripts
python -m json.tool rules/dnd5e/core.json
python -m json.tool rules/dnd5e/skills.json
```

## 接口约定

- 前缀：`/api/v1`
- 成功响应：`{"code": 0, "message": "ok", "data": ...}`
- 业务错误：通过 `StoryForgeError` 统一映射
- AI 无 Key：走 mock/fallback 路径，便于本地演示

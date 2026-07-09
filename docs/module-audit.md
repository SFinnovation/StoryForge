# 模块检查报告

> 更新日期：2026-07-09  
> 范围：按当前仓库文件结构核对实现状态、验收要求、可演示能力与风险。

## 总体结论

StoryForge 当前已达到“可现场运行、可区分登录角色、可做数据增删改查/状态变更、可展示后端统计图表、可演示核心特色技术”的答辩版本。

最适合答辩展示的主线是：

```text
普通用户登录
  -> 创建角色
  -> 创建/加入多人房间
  -> 全员准备后开局
  -> AI DM 开场
  -> 聊天 / 行动 / 骰点 / AI 旁白 / DM 提问
  -> 管理员登录
  -> 查看统计图表、管理世界观/模组、用户和会话
```

## 验收要求对照

| 验收内容 | 当前实现 | 推荐演示入口 |
|---|---|---|
| 项目运行 | 后端 FastAPI + 前端 Vite 可本地启动；AI Key 可为空走 fallback。 | `uvicorn backend.app.main:app --reload --port 8000`，`npm run dev`。 |
| 登录角色 | 普通用户/游客进入玩家侧；管理员进入 `AdminPage`；封禁用户不可继续使用。 | 普通账号和 `admin/admin123` 分别登录。 |
| 数据操作 | 世界观/模组创建、启用、停用；用户封禁/解封；会话归档；房间创建/加入/结束。 | 管理员后台 + 玩家房间页。 |
| 数据可视化 | 管理后台统计卡与世界活跃度图表来自 `/admin/summary`；房间页展示进度、团队同步、线索/任务/行动统计。 | `AdminPage.vue` 与 `GameRoomPage.vue` 右侧面板。 |
| 特色技术 | AI DM 多 Agent 编排、后端 d20 判定、WebSocket 多人实时、可恢复房间事件流、DM 提问隐私过滤。 | 提交一次行动，展示骰点、AI 旁白、后台数据落库。 |
| 真实需求 | 解决传统跑团组织成本高、DM 稀缺、记录分散、线上协同弱的问题。 | PPT 背景页 + 系统演示。 |
| Vibe 日志 | 多轮迭代从单人 AI 跑团扩展到多人房间、管理后台、前端联调与 E2E 验证。 | PPT “关键迭代过程”页。 |
| 代码理解 | 小组成员可分别讲清前端状态流、房间实时协议、AI 行动流水线、数据库模型。 | PPT 分工页 + 技术页。 |

## 文件结构映射

```text
StoryForge/
├─ backend/
│  ├─ app/api/v1/          # REST 与 WebSocket 路由
│  ├─ app/ai/              # AI Agent、Prompt、Schema、fallback
│  ├─ app/core/            # 配置、异常
│  ├─ app/db/              # 数据库连接、建表、种子
│  ├─ app/models/          # ORM 模型
│  ├─ app/repositories/    # 仓储层
│  ├─ app/schemas/         # API DTO
│  └─ app/services/        # 业务服务、房间实时、AI 编排、后台统计
├─ frontend/
│  ├─ src/api/             # REST client 与 WebSocket client
│  ├─ src/*.vue            # 玩家侧与管理员侧页面
│  └─ public/dice/         # 骰点视频资源
├─ rules/dnd5e/            # D&D 5e 规则 JSON
├─ docs/                   # 项目文档与答辩材料指导
└─ backend.md              # 后端接口快照
```

## 后端模块检查

| 模块 | 文件 | 状态 |
|---|---|---|
| API 聚合 | `backend/app/api/v1/router.py` | 已挂载 auth、admin、rooms、ws_rooms、sessions、worlds、characters、content 等。 |
| 认证 | `auth.py`、`auth_service.py` | 注册、登录、游客、当前用户、登出；自定义 Bearer token；封禁状态校验。 |
| 多人房间 REST | `rooms.py` | 建房、列表、加入、离开、准备、选角、开局、结束、历史、HTTP 回退消息/行动/DM 提问。 |
| WebSocket | `ws_rooms.py`、`websocket_manager.py` | 房间实时连接、在线状态、聊天、场外、行动、DM 提问、typing、ping。 |
| 房间生命周期 | `room_service.py`、`room_member_service.py` | 房间码、成员、角色绑定、满员开局、host 权限、离开转让。 |
| 多人行动 | `room_action_service.py` | 房间级锁、行动幂等、AI 流水线复用、骰点/旁白/状态事件广播。 |
| DM 提问 | `guidance_service.py` | `visibility=self/room`，私密问答历史过滤。 |
| 单人会话 | `sessions.py`、`session_service.py` | 单人闭环保留，可用于兼容与调试。 |
| 管理员后台 | `admin.py` | 统计、世界观/模组、用户、会话、日志接口。 |
| 数据库 | `models.py`、`init_db.py`、`schema.sql` | ORM 覆盖房间、会话、AI、后台等表；启动自动建表/补列。 |
| 内容导入 | `content.py`、`content_ingestion_service.py` | 规则书/模组抽取与内容包存储已具备，AKP 为后续增强。 |

## 前端模块检查

| 模块 | 文件 | 状态 |
|---|---|---|
| 应用壳 | `App.vue` | 登录态、页面状态、管理员分流、房间/结局状态已接入。 |
| API 客户端 | `api/client.js` | auth/worlds/characters/rooms/sessions/admin 均已封装。 |
| WS 客户端 | `api/wsClient.js` | 自动重连、心跳、seq 去重、聊天/行动/DM 提问发送方法。 |
| 登录注册 | `LoginRegister.vue` | 登录、注册、游客进入。 |
| 大厅 | `HomePage.vue` | 读取世界观、角色、房间、会话；创建/加入/继续/档案入口。 |
| 角色创建 | `RolePage.vue` | 三阶段角色创建，支持 D&D MVP 属性与技能。 |
| 多人房间 | `GameRoomPage.vue` | 当前核心演示页：实时消息、行动、骰点动画、DM 提问、成员状态、统计面板。 |
| 结局页 | `EndingPage.vue` | 房间结束后的结果展示。 |
| 档案页 | `ArchivePage.vue` | 历史会话读取与展示。 |
| 管理后台 | `AdminPage.vue` | 统计卡、世界活跃度图表、世界观/模组、用户、会话管理。 |

## 数据库与数据可视化检查

| 数据来源 | 用途 | 前端展示 |
|---|---|---|
| `users` | 登录、角色差异、封禁、用户统计。 | 登录态、后台用户列表。 |
| `rooms`、`room_members` | 房间状态、成员、准备、在线、房间统计。 | 房间页、后台活跃房间。 |
| `room_messages` | 群聊、场外、行动、骰点、AI 旁白、DM 建议。 | 房间消息流、断线补消息、后台消息统计。 |
| `room_actions` | 玩家行动处理记录。 | 后台待处理行动统计。 |
| `game_sessions`、`messages` | 跑团主日志与历史会话。 | 档案页、后台会话记录。 |
| `action_checks` | d20 判定结果。 | 房间骰点消息与行动结果。 |
| `facts`、`clues`、`tasks`、`ai_reviews` | AI 上下文、线索、任务、审核结果。 | 房间统计、调试接口、后续可视化扩展。 |
| `worlds`、`world_modules` | 世界观与模组管理。 | 世界观页、后台树形管理、活跃度图表。 |

## 特色技术检查

1. AI DM 多 Agent 编排：`OpeningAgent -> ActionParserAgent -> rule_service -> NarrativeAgent -> CriticAgent -> RevisionLoop -> StateCommitter`。
2. AI 与规则解耦：AI 负责理解和叙事，行动成败由后端 `rule_service` 根据 D&D 数据计算。
3. WebSocket 实时协同：同房间玩家实时收到聊天、行动、骰点、AI 旁白、在线状态。
4. 事件流可恢复：`room_messages.seq` 支持刷新/断线后按 `after_seq` 补齐。
5. DM 提问不剧透：`GuidanceAgent` 不推进剧情，私密提问只对本人可见。
6. 管理后台后端可视化：统计卡和图表直接来自数据库聚合接口。

## 推荐验证记录

| 命令 | 目的 |
|---|---|
| `.venv\Scripts\python.exe -m compileall -q backend/app backend/scripts scripts` | Python 语法检查。 |
| `.venv\Scripts\python.exe -m backend.scripts.test_room_flow` | 多人房间服务层全链路冒烟。 |
| `.venv\Scripts\python.exe -m backend.scripts.e2e_multiplayer_api --spawn-server` | HTTP + WebSocket 端到端验证。 |
| `.venv\Scripts\python.exe -m backend.scripts.test_admin_api` | 管理员接口验证。 |
| `.venv\Scripts\python.exe -m backend.scripts.test_frontend_contract` | 前端契约接口验证。 |
| `cd frontend && npm.cmd run build` | 前端构建验证。 |

## 优先级建议

1. 答辩前固定演示数据：准备 2 个普通账号、1 个管理员账号、2 个角色、1 个 max_players=2 的房间。
2. 若现场网络不稳定，保持 `LLM_API_KEY` 为空使用 fallback，保证系统闭环稳定。
3. 答辩 PPT 中明确说明“当前 WebSocket 为单进程版本，生产多实例需 Redis Pub/Sub + 分布式锁”。
4. 继续增强 D&D 角色规则、报告导出、管理员操作日志前端展示、CI 自动验证。

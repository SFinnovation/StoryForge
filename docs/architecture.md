# 架构设计

> 更新日期：2026-07-09  
> 本文按当前仓库实现描述 StoryForge 的真实架构，而不是早期规划稿。

## 总览

StoryForge 采用前后端分离的 monorepo 架构。前端负责登录、大厅、角色创建、多人房间与管理后台；后端负责鉴权、房间生命周期、WebSocket 实时通信、规则判定、AI 编排和数据持久化。

```text
Vue 3 + Vite
  ├─ HTTP fetch: auth / worlds / characters / rooms / sessions / admin
  └─ WebSocket: /api/v1/ws/rooms/{room_id}
        |
        v
FastAPI /api/v1
  ├─ REST Routers
  ├─ WebSocket Router
  ├─ Services: room / member / chat / action / guidance / admin / report
  ├─ AI Orchestrator: opening / action parse / narrative / critic / summary / guidance
  ├─ Repositories
  └─ SQLAlchemy ORM -> SQLite

rules/dnd5e/*.json -> rule_service -> character creation / action checks
```

## 分层职责

| 层级 | 路径 | 职责 |
|---|---|---|
| 前端页面 | `frontend/src/*.vue` | 登录注册、大厅、世界观、角色创建、多人房间、结局、档案、管理员后台。 |
| 前端通信 | `frontend/src/api/client.js`、`wsClient.js` | REST 请求、token 存取、WebSocket 重连、心跳、seq 去重。 |
| API 层 | `backend/app/api/v1/` | FastAPI 路由，统一返回 `ApiResponse`。 |
| 实时层 | `ws_rooms.py`、`websocket_manager.py`、`realtime_service.py` | 房间连接池、事件信封、广播、在线状态。 |
| 业务服务 | `backend/app/services/` | 房间、成员、聊天、行动、DM 提问、会话、报告、内容导入、管理员统计。 |
| AI 模块 | `backend/app/ai/` | Agent、Prompt、Schema、LLM Client、fallback、修订循环。 |
| 仓储层 | `backend/app/repositories/` | 对 Message、Fact、Room、Action、Report 等表的读写封装。 |
| 数据模型 | `backend/app/models/models.py` | SQLAlchemy ORM，与 `init_db.py` 自动建表/补列配合。 |
| 规则数据 | `rules/dnd5e/` | D&D 5e 规则 JSON，供角色创建和 d20 判定使用。 |

## 核心业务闭环

```text
用户登录/游客进入
  -> 大厅读取 worlds / characters / rooms / sessions
  -> 创建角色（D&D MVP 规则校验）
  -> 创建房间或输入房间码加入
  -> room_members 绑定角色并准备
  -> 房主开局
     -> 创建 game_sessions(mode=multiplayer)
     -> build_for_opening
     -> OpeningAgent
     -> commit_opening + seed_session_world_data
     -> room_messages 镜像 + WebSocket 广播
  -> 玩家在房间聊天、场外讨论、提交行动或 dm.ask
  -> action.submit
     -> 房间级 asyncio.Lock
     -> RoomAction 幂等记录
     -> run_action_pipeline
     -> ActionParserAgent + rule_service d20 判定
     -> NarrativeAgent + Critic + RevisionLoop
     -> StateCommitter
     -> room_messages(action/dice/narration) + WebSocket 广播
  -> 结局或房主结束
  -> 历史档案 / 管理员后台可查询数据
```

## 多人实时设计

当前多人能力不是单纯 UI 原型，已经落地为后端 REST + WebSocket + 前端页面：

- `rooms`：房间主体，含房间码、世界观、房主、状态、人数上限、当前会话。
- `room_members`：成员、角色绑定、host/player/spectator、在线状态、准备状态。
- `room_messages`：房间事件流，保存聊天、场外、行动、骰点、AI 旁白、DM 建议；用 `seq` 保证排序与断线补消息。
- `room_actions`：行动处理记录，支持幂等和后续队列扩展。
- `ws_rooms.py`：支持 `chat.send`、`ooc.send`、`action.submit`、`dm.ask`、typing、ping。
- `GameRoomPage.vue`：展示成员、房间状态、消息流、行动输入、DM 提问、右侧功能面板和 d20 视频动画。

房间行动使用房间级锁串行处理，避免两个玩家同时触发 AI 叙事造成上下文交错。普通聊天不受锁影响。

## 数据流与可视化来源

答辩时建议展示两条数据流。

### 玩家行动数据流

```text
GameRoomPage 输入行动
  -> wsClient action.submit
  -> ws_rooms._dispatch
  -> room_action_service.handle_action
  -> run_action_pipeline
  -> rule_service.roll_check
  -> StateCommitter 写 messages/action_checks/facts/ai_reviews
  -> chat_service 写 room_messages
  -> WebSocket 广播 dice.result / dm.narration / state.updated
  -> 前端消息流、骰点动画、进度统计更新
```

### 管理后台数据流

```text
AdminPage
  -> adminApi.summary/worlds/users/sessions
  -> backend/app/api/v1/admin.py
  -> SQLAlchemy 聚合 users/rooms/game_sessions/messages/room_messages/room_actions/worlds
  -> 统计卡片 + 世界活跃度图表 + 用户/会话列表
```

## 特色技术点

| 技术点 | 落地位置 | 价值 |
|---|---|---|
| AI DM 多 Agent 编排 | `backend/app/ai/`、`action_service.py` | 把“理解行动、规则判定、叙事、审核修订”拆成可控流水线。 |
| 后端规则判定 | `rule_service.py`、`rules/dnd5e/` | AI 不直接决定成败，保证演示中的公平性和可解释性。 |
| 房间实时协议 | `ws_rooms.py`、`wsClient.js` | 实现多人聊天、行动、骰点、AI 旁白实时同步。 |
| 可恢复事件流 | `room_messages.seq` | 刷新或断线后可通过 `after_seq` 补齐消息。 |
| DM 提问隐私控制 | `guidance_service.py` | `visibility=self` 的问答只给提问者，历史查询也过滤。 |
| 管理端数据聚合 | `admin.py`、`AdminPage.vue` | 直接从后端数据库生成统计卡和图表，满足验收的数据可视化要求。 |

## 现有边界与技术债

- 当前 token 是项目自定义 Bearer token，生产环境建议替换为标准 JWT、刷新 token 与更完整 RBAC。
- WebSocket 连接池和房间锁是单进程内存实现，多实例部署需 Redis Pub/Sub 与分布式锁。
- `game_sessions.character_id` 在多人模式下仍保存房主/代表角色，长期可迁移为可空并完全依赖 `room_members.character_id`。
- PDF 导出仍未完成，Markdown 导出可用。
- D&D 角色创建是 MVP，复杂种族分支、27 点购、完整职业成长仍可继续扩展。

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-09 | 按当前多人房间、WebSocket、管理员前端与数据可视化实现重写。 |
| 2026-07-08 | 管理员后台与 AKP/多人设计补充。 |

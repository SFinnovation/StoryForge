# 后端接口与实现快照

> 更新日期：2026-07-09  
> 范围：FastAPI 后端、数据库、AI 编排、多人房间、管理员后台与验证脚本。

## 当前结论

后端已经形成可演示的多人 AI 跑团主闭环：

```text
POST /auth/login 或 /auth/guest
  -> 创建/读取角色
  -> POST /rooms 创建房间
  -> POST /rooms/join 加入房间
  -> POST /rooms/{id}/character 绑定角色
  -> POST /rooms/{id}/ready 全员准备
  -> POST /rooms/{id}/start
     -> GameSession(mode=multiplayer)
     -> OpeningAgent
     -> commit_opening + world_seed
     -> room_messages + WebSocket 广播
  -> WebSocket chat.send / ooc.send / action.submit / dm.ask
     -> room_action_service
     -> run_action_pipeline
     -> 后端 d20 判定
     -> Narrative + Critic + RevisionLoop
     -> messages/action_checks/facts/ai_reviews/room_messages
  -> POST /rooms/{id}/end
```

单人 `/sessions/*` 闭环仍保留，可作为兼容接口与后端验证入口。

## 路由分组

| 路由文件 | 前缀 | 职责 |
|---|---|---|
| `auth.py` | `/api/v1/auth` | 注册、登录、游客、当前用户、登出。 |
| `rooms.py` | `/api/v1/rooms` | 建房、加入、准备、选角、开局、结束、历史、HTTP 回退聊天/行动/DM 提问。 |
| `ws_rooms.py` | `/api/v1/ws/rooms/{room_id}` | 房间 WebSocket 实时事件通道。 |
| `admin.py` | `/api/v1/admin` | 管理员统计、世界观/模组、用户、会话、操作日志。 |
| `sessions.py` | `/api/v1/sessions` | 单人会话、行动、消息、报告、facts、ai_reviews。 |
| `characters.py` | `/api/v1/characters` | 角色创建、列表、详情，支持 D&D MVP payload。 |
| `worlds.py` | `/api/v1/worlds` | 世界观列表与详情。 |
| `rules.py` | `/api/v1/rules` | D&D 5e 规则摘要、技能列表。 |
| `content.py` | `/api/v1/content` | 规则书/模组内容抽取与内容包相关能力。 |
| `stories.py`、`chapters.py`、`worldbuilding.py`、`export.py` | `/api/v1/*` | 保留通用故事创作、章节、设定与导出能力。 |

## 多人房间 REST

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/v1/rooms` | 创建房间，创建者自动成为 host。 |
| `GET` | `/api/v1/rooms?scope=mine/public` | 查询我的房间或公开房间。 |
| `POST` | `/api/v1/rooms/join` | 通过 `room_code` 加入房间，可携带角色与显示名。 |
| `GET` | `/api/v1/rooms/{room_id}` | 房间详情、成员、进度统计。 |
| `POST` | `/api/v1/rooms/{room_id}/character` | 绑定房间内角色。 |
| `POST` | `/api/v1/rooms/{room_id}/ready` | 准备/取消准备。 |
| `POST` | `/api/v1/rooms/{room_id}/start` | 房主开局，要求房间满员、全员选角、全员准备。 |
| `POST` | `/api/v1/rooms/{room_id}/end` | 房主结束房间与当前会话。 |
| `GET` | `/api/v1/rooms/{room_id}/messages` | 房间事件流分页，支持 `before_seq`、`after_seq`。 |
| `POST` | `/api/v1/rooms/{room_id}/chat` | HTTP 回退群聊。 |
| `POST` | `/api/v1/rooms/{room_id}/ooc` | HTTP 回退场外消息。 |
| `POST` | `/api/v1/rooms/{room_id}/ask` | HTTP 回退 DM 提问。 |
| `POST` | `/api/v1/rooms/{room_id}/action` | HTTP 回退行动提交。 |

## WebSocket 协议

连接地址：

```text
ws://localhost:8000/api/v1/ws/rooms/{room_id}?token=<access_token>
```

客户端事件：

| type | data | 说明 |
|---|---|---|
| `chat.send` | `{content, client_msg_id}` | 房间群聊。 |
| `ooc.send` | `{content, client_msg_id}` | 场外讨论。 |
| `action.submit` | `{action_text, client_msg_id}` | 触发 AI DM 行动流水线。 |
| `dm.ask` | `{question, client_msg_id, visibility}` | 向 DM 提问，不推进剧情。 |
| `typing.start` / `typing.stop` | `{}` | 打字状态，不落库。 |
| `ping` | `{}` | 心跳。 |

服务端事件使用统一信封：

```json
{
  "v": 1,
  "type": "dm.narration",
  "room_id": 1,
  "seq": 12,
  "ts": "2026-07-09T00:00:00Z",
  "actor": null,
  "data": {}
}
```

常见广播：`room.snapshot`、`room.updated`、`game.started`、`member.online/offline`、`chat.message`、`ooc.message`、`action.accepted`、`action.received`、`ai.thinking`、`dice.result`、`dice.rolled`、`dm.narration`、`ai.narration`、`dm.guidance`、`state.updated`、`game.ended`。

## 数据库模型

核心表：

- 用户与权限：`users`、`admin_operation_logs`
- 世界观与内容：`worlds`、`world_modules`、`rulebook_packs`、`adventure_modules` 等内容包相关表
- 角色与会话：`characters`、`game_sessions`
- 单局日志：`messages`、`action_checks`、`clues`、`tasks`、`reports`
- AI 记忆与审核：`facts`、`npc_profiles`、`ai_reviews`
- 多人房间：`rooms`、`room_members`、`room_messages`、`room_actions`

`game_sessions` 已扩展 `room_id`、`mode`、`host_user_id`。多人模式中，真实“玩家-角色”映射由 `room_members.character_id` 维护。

## AI 与规则

| 模块 | 文件 | 说明 |
|---|---|---|
| AI 门面 | `backend/app/ai/orchestrator.py`、`services/ai_service.py` | 统一调用 Opening、ActionParser、Narrative、Summary、Guidance。 |
| 行动流水线 | `services/action_service.py` | 抽出 `run_action_pipeline`，供单人和多人复用。 |
| 多人行动 | `services/room_action_service.py` | 房间锁、幂等、RoomAction、房间消息镜像、事件广播。 |
| DM 提问 | `services/guidance_service.py` | 不推进剧情，支持 `visibility=self/room` 与私密历史过滤。 |
| 规则判定 | `services/rule_service.py` + `rules/dnd5e/*.json` | 后端执行 d20、熟练、属性修正与 DC 判断。 |
| 状态提交 | `services/state_committer.py` | 写入消息、检定、线索、任务、Fact、AI Review。 |

## 管理员能力

管理员接口要求 Bearer token 对应用户 `role=admin` 且 `status=active`。

已实现：

- `/admin/summary`：用户、房间、会话、消息、行动、世界活跃度等统计。
- `/admin/worlds`：世界观列表、创建、启用、停用。
- `/admin/worlds/{id}/modules`、`/admin/modules/{id}`：模组创建、启用、停用。
- `/admin/sessions`、`/admin/sessions/{id}`、`/admin/sessions/{id}/dissolve`：会话查询与强制归档。
- `/admin/users`、`/admin/users/{id}/ban`、`/admin/users/{id}/unban`、`/admin/users/{id}/reset-password`：用户管理。
- `/admin/operation-logs`：管理员操作日志。

## 验证脚本

```powershell
.venv\Scripts\python.exe -m backend.scripts.test_room_flow
.venv\Scripts\python.exe -m backend.scripts.e2e_multiplayer_api --spawn-server
.venv\Scripts\python.exe -m backend.scripts.test_admin_api
.venv\Scripts\python.exe -m backend.scripts.test_frontend_contract
.venv\Scripts\python.exe -m backend.scripts.verify_ai_db_interaction
.venv\Scripts\python.exe -m backend.scripts.verify_repositories
.venv\Scripts\python.exe -m compileall -q backend/app backend/scripts scripts
```

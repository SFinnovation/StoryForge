# 管理员后台说明

> 更新日期：2026-07-09  
> 范围：管理员后台前端、后端接口、数据库统计来源、验收演示方式。

## 当前状态

管理员后台已经完成前后端闭环。管理员账号登录后，前端 `App.vue` 会根据 `currentUser.role === 'admin'` 自动进入 `AdminPage.vue`，普通用户进入玩家侧大厅。

管理员接口统一挂载在 `/api/v1/admin` 下，要求 Bearer token 对应用户满足：

- `role=admin`
- `status=active`

开发环境默认管理员账号由 `.env` 控制：

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

后端启动执行 `init_db()` 时会自动确保默认管理员存在。

## 数据库变更

- `users.email`、`users.status`、`users.role`、`users.is_temporary`：用于用户管理、封禁和角色差异。
- `world_modules`：世界观下的模组管理，停用使用 `is_enabled=0`。
- `admin_operation_logs`：记录管理员操作。
- 管理员统计还会聚合 `rooms`、`room_members`、`room_messages`、`room_actions`、`game_sessions`、`messages`、`reports`。

## 前端页面

文件：`frontend/src/AdminPage.vue`

主要区域：

| 区域 | 数据来源 | 说明 |
|---|---|---|
| 统计卡片 | `GET /admin/summary` | 今日新增会话、活跃房间、历史会话、消息与行动、用户档案、世界观/模组。 |
| 世界活跃度图表 | `summary.world_activity` | 按世界观展示房间数、会话数、消息数等后端聚合数据。 |
| 世界观/模组树 | `GET /admin/worlds?include_disabled=true` | 上架世界观、创建模组、启用/停用世界观和模组。 |
| 用户列表 | `GET /admin/users` | 查看用户，封禁/解封非管理员账号。 |
| 会话记录 | `GET /admin/sessions` | 查看用户会话，强制归档异常会话。 |

这部分是答辩中展示“登录角色差异”“数据操作”“数据可视化来自后端”的推荐入口。

## 接口概览

### 概览统计

```http
GET /api/v1/admin/summary
```

返回字段包括：

- 用户：`users`、`banned_users`、`temporary_users`
- 世界观/模组：`worlds`、`disabled_worlds`、`modules`、`disabled_modules`
- 会话：`sessions`、`active_sessions`、`today_sessions`、`reports`
- 房间：`rooms`、`active_rooms`、`room_members`
- 消息与行动：`room_messages`、`session_messages`、`pending_actions`
- 图表数据：`world_activity`
- 数据库状态：`database_status`

### 世界观/模组管理

```http
GET    /api/v1/admin/worlds
POST   /api/v1/admin/worlds
POST   /api/v1/admin/worlds/{world_id}/enable
DELETE /api/v1/admin/worlds/{world_id}
POST   /api/v1/admin/worlds/{world_id}/modules
POST   /api/v1/admin/modules/{module_id}/enable
DELETE /api/v1/admin/modules/{module_id}
```

删除实际为停用：`is_enabled=0`。创建、启用、停用都会写入 `admin_operation_logs`。

### 会话记录管理

```http
GET  /api/v1/admin/sessions
GET  /api/v1/admin/sessions/{session_id}
POST /api/v1/admin/sessions/{session_id}/dissolve
```

列表支持 `owner_id`、`status`、`world_id`、`keyword`、`created_from`、`created_to`、`skip`、`limit`。强制归档会将会话状态置为 `archived`，写入系统消息，并记录管理员操作日志。

### 用户管理

```http
GET  /api/v1/admin/users
POST /api/v1/admin/users/{user_id}/reset-password
POST /api/v1/admin/users/{user_id}/ban
POST /api/v1/admin/users/{user_id}/unban
```

用户列表支持 `user_id`、`nickname`、`email`、`status`、`role`、`keyword`、`skip`、`limit`。管理员不能封禁当前管理员自己。

### 操作日志

```http
GET /api/v1/admin/operation-logs
```

支持按 `admin_id`、`action`、`target_type`、`target_id` 和分页查询。

## 演示建议

1. 用普通账号登录，展示玩家大厅、房间、行动。
2. 退出后用管理员账号登录，展示界面自动切换为后台。
3. 在后台展示统计卡片和世界活跃度图表，说明图表来自 `/admin/summary` 的数据库聚合。
4. 新增一个世界观或模组，再停用它，说明 CRUD/状态变更写入后端。
5. 封禁/解封一个普通用户，展示登录角色与权限差异。
6. 打开某用户会话记录，展示管理员可追踪历史会话。

## 验证方式

```powershell
.venv\Scripts\python.exe -m backend.scripts.test_admin_api
.venv\Scripts\python.exe -m backend.scripts.test_frontend_contract
.venv\Scripts\python.exe -m compileall -q backend/app backend/scripts scripts
```

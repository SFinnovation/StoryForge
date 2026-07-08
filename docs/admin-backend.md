# 管理员后台后端说明

> 更新日期：2026-07-08  
> 范围：管理员后台所需的数据库结构、鉴权约束、API 契约与验证方式。当前仅完成后端与数据库逻辑，管理员前端页面等待后续接入。

## 当前状态

管理员后台后端已完成第一版可对接能力，接口统一挂载在 `/api/v1/admin` 下。所有管理员接口都要求 Bearer token 对应用户 `role=admin` 且账号 `status=active`。

开发环境默认管理员账号由环境变量控制：

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

后端启动执行 `init_db()` 时会自动确保默认管理员存在。

## 数据库变更

- `users`：新增 `email`、`status`。`status` 支持 `active` / `banned`，封禁用户无法登录。
- `world_modules`：世界观下的模组表，删除采用 `is_enabled=0` 软删除。
- `admin_operation_logs`：管理员操作日志表，记录管理员 ID、操作类型、目标类型、目标 ID、描述和时间。

## 接口概览

### 概览统计

```http
GET /api/v1/admin/summary
```

返回用户数、封禁用户数、世界观数、模组数、会话数、进行中会话数、结局报告数。

### 世界观/模组管理

```http
GET    /api/v1/admin/worlds
POST   /api/v1/admin/worlds
DELETE /api/v1/admin/worlds/{world_id}
POST   /api/v1/admin/worlds/{world_id}/modules
DELETE /api/v1/admin/modules/{module_id}
```

创建世界观时可同时传入 `modules` 数组。删除世界观和模组都会写入 `admin_operation_logs`。

### 会话记录管理

```http
GET  /api/v1/admin/sessions
GET  /api/v1/admin/sessions/{session_id}
POST /api/v1/admin/sessions/{session_id}/dissolve
```

列表支持 `owner_id`、`status`、`world_id`、`keyword`、`created_from`、`created_to`、`skip`、`limit`。强制解散会将会话状态置为 `archived`，写入系统消息，并记录管理员操作日志。

### 用户管理

```http
GET  /api/v1/admin/users
POST /api/v1/admin/users/{user_id}/reset-password
POST /api/v1/admin/users/{user_id}/ban
POST /api/v1/admin/users/{user_id}/unban
```

用户列表支持 `user_id`、`nickname`、`email`、`status`、`role`、`keyword`、`skip`、`limit`。当前用户返回包含 `password_hash`，满足后台管理查看数据结构的需求，前端展示时应谨慎处理。

### 系统管理

```http
GET /api/v1/admin/operation-logs
```

支持按 `admin_id`、`action`、`target_type`、`target_id` 和分页查询。

## 验证方式

```powershell
.venv\Scripts\python.exe -m backend.scripts.test_admin_api
.venv\Scripts\python.exe -m backend.scripts.test_frontend_contract
.venv\Scripts\python.exe -m compileall backend
```

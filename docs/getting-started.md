# 快速开始

> 更新日期：2026-07-09  
> 本文说明如何在本地准备、运行和验证 StoryForge。

## 前置要求

- Git 2.30+
- Python 3.11+
- Node.js 20+ 与 npm

Windows PowerShell 如果拦截 `npm.ps1`，请使用：

```powershell
npm.cmd install
npm.cmd run dev
```

## 环境变量

当前仓库根目录已经有本地 `.env`，如果需要重新生成，可从后端模板复制到根目录：

```powershell
Copy-Item backend\.env.example .env
```

常用配置：

```env
DATABASE_URL=sqlite:///./storyforge.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=
LLM_MODEL=deepseek-chat
```

`LLM_API_KEY` 可以留空。留空时后端使用 fallback 生成开局、行动叙事和 DM 建议，适合现场演示。

## 启动后端

从仓库根目录执行：

```powershell
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

后端启动时会执行 `init_db()`，自动建表、补列并确保开发管理员账号存在。

验证：

```powershell
curl http://localhost:8000/health
```

浏览器访问：

- http://localhost:8000/health
- http://localhost:8000/docs

## 启动前端

```powershell
cd frontend
npm install
npm run dev
```

访问：

- http://localhost:5173

`frontend/vite.config.js` 会把 `/api` 代理到后端开发服务，前端默认 `API_BASE_URL=/api/v1`。

## 默认账号与角色

管理员：

```text
username: admin
password: admin123
```

普通用户可以在登录页注册，也可以使用游客进入。管理员登录后会自动进入后台，普通用户进入玩家大厅。

## 推荐演示流程

1. 启动后端和前端。
2. 用两个普通账号分别登录两个浏览器窗口。
3. 每个账号创建或选择一个角色。
4. A 创建房间，人数设置为 2。
5. B 输入房间码加入。
6. 两人绑定角色并准备。
7. 房主开局，观察 AI DM 开场广播。
8. 玩家发送群聊与场外消息。
9. 玩家提交行动，观察 `ai.thinking`、骰点动画、AI 旁白。
10. 玩家向 DM 提问，观察私密建议。
11. 用管理员账号登录，查看统计卡、世界活跃图表、用户与会话管理。

## 验证脚本

后端服务层多人房间验证：

```powershell
.venv\Scripts\python.exe -m backend.scripts.test_room_flow
```

多人 HTTP + WebSocket 端到端验证，可自动拉起服务：

```powershell
.venv\Scripts\python.exe -m backend.scripts.e2e_multiplayer_api --spawn-server
```

管理员接口验证：

```powershell
.venv\Scripts\python.exe -m backend.scripts.test_admin_api
```

前端契约验证：

```powershell
.venv\Scripts\python.exe -m backend.scripts.test_frontend_contract
```

静态检查：

```powershell
.venv\Scripts\python.exe -m compileall -q backend/app backend/scripts scripts
.venv\Scripts\python.exe -m json.tool rules/dnd5e/core.json
.venv\Scripts\python.exe -m json.tool rules/dnd5e/skills.json
```

前端构建：

```powershell
cd frontend
npm.cmd run build
```

## 常见问题

### 管理员登录后看不到玩家大厅

这是预期行为。管理员会被 `App.vue` 分流到 `AdminPage.vue`，用于展示角色差异与后台管理。

### 房主点击开始失败

当前房间开局要求：

- 房间状态为 `waiting`
- 房间人数达到 `max_players`
- 全员已绑定角色
- 全员已准备
- 当前用户是房主

演示时建议将房间人数设置为实际测试账号数量。

### WebSocket 连接失败

确认：

- 后端运行在 `localhost:8000`
- 前端通过 Vite 代理访问 `/api/v1`
- 当前用户已经是房间成员
- 浏览器控制台没有 token 过期或 403 错误

### AI 响应慢或失败

现场演示可留空 `LLM_API_KEY` 使用 fallback，避免外部网络影响。接入真实模型时再配置 `LLM_API_BASE`、`LLM_API_KEY`、`LLM_MODEL`。

## 下一步阅读

- [架构设计](architecture.md)
- [前端结构与交互逻辑](frontend-structure.md)
- [管理员后台说明](admin-backend.md)
- [模块检查报告](module-audit.md)
- [答辩 PPT 生成指导](defense-ppt-generation-guide.md)

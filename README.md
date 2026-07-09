# StoryForge

StoryForge（灵境档案）是一个面向桌面浏览器的 AI 跑团互动与推理系统。项目已经从“通用故事创作工具”收敛为“多人房间 + AI DM + 后端规则判定 + 跑团日志持久化 + 管理员后台”的 Web 跑团平台。

当前主流程：

```text
登录 / 游客进入
  -> 选择或创建角色
  -> 创建 / 加入多人房间
  -> 全员选角、准备、房主开局
  -> AI DM 生成开场
  -> 玩家聊天 / 场外交流 / 提交行动 / 向 DM 提问
  -> 后端 d20 规则判定 + AI 叙事推进
  -> 房间消息、会话消息、骰点、线索、任务、AI 审核持久化
  -> 结局页与历史档案
```

## 当前状态

| 模块 | 状态 | 说明 |
|---|---|---|
| 前端应用 | 已接入主流程 | Vue 3 + Vite，包含登录注册、大厅、世界观、角色创建、多人房间、结局页、档案页、管理员后台。 |
| 多人房间 | 已实现 P0/P1 核心 | REST 建房/加入/准备/选角/开局/结束，WebSocket 实时聊天、场外消息、行动、DM 提问、在线状态、断线补消息。 |
| AI DM | 已实现 | Opening、ActionParser、Narrative、Critic、RevisionLoop、Summary、Guidance；无 Key 时走 fallback，便于本地演示。 |
| 规则判定 | 已实现 MVP | D&D 5e 静态规则 JSON，行动由 AI 解析意图，后端执行 d20 检定与结果计算。 |
| 数据持久化 | 已实现 | SQLite + SQLAlchemy，覆盖用户、角色、世界观、会话、消息、房间、房间消息、行动、报告、Fact、NPC、AI Review 等。 |
| 管理员后台 | 已实现前后端 | 管理员登录后自动进入 `AdminPage`，可查看数据概览、世界观/模组、用户、会话记录，并执行封禁/启用/归档等操作。 |
| 数据可视化 | 已实现基础图表 | 管理端统计卡与世界活跃度图表来自 `/api/v1/admin/summary`；房间页展示进度、团队同步、线索/任务/行动统计。 |
| 内容知识导入 | 部分实现 | 规则书/冒险模组抽取与内容包仓储已存在；AKP 知识包集成仍是可选增强路线。 |

## 快速开始

后端：

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

访问地址：

- 后端健康检查：http://localhost:8000/health
- API 文档：http://localhost:8000/docs
- 前端开发服务：http://localhost:5173

开发环境默认管理员账号由 `.env` 控制：

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

AI 密钥可以留空；留空时系统会使用本地 fallback 叙事，仍可完成演示闭环。

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | Vue 3、Vite、原生 fetch、WebSocket |
| 后端 | FastAPI、SQLAlchemy、Pydantic |
| 数据库 | SQLite（开发演示），可按部署需要迁移到 MySQL/PostgreSQL |
| AI | OpenAI 兼容 Chat Completions API，默认按 DeepSeek 配置预留 |
| 规则数据 | D&D 5e SRD JSON |
| 实时通信 | FastAPI WebSocket，房间级连接池与房间级行动锁 |

## 项目结构

```text
StoryForge/
├─ backend/
│  ├─ app/api/v1/          # FastAPI 路由：auth、rooms、ws_rooms、admin、sessions 等
│  ├─ app/ai/              # Agent、Prompt、Schema、LLM Client、fallback
│  ├─ app/models/          # SQLAlchemy ORM
│  ├─ app/services/        # 业务服务、AI 编排、房间实时服务、管理员服务
│  ├─ app/repositories/    # 仓储层
│  └─ scripts/             # 后端验证与端到端脚本
├─ frontend/
│  ├─ src/                 # Vue 页面与 API/WebSocket 客户端
│  ├─ public/dice/         # d20 骰点视频资源
│  ├─ 背景/ 图标/ 游戏种类/ # 视觉资源
│  └─ package.json
├─ rules/dnd5e/            # D&D 5e 静态规则 JSON
├─ docs/                   # 架构、前端、AI、多人房间、答辩 PPT 指导等文档
├─ scripts/                # 项目级脚本
└─ backend.md              # 后端接口与验证快照
```

## 核心文档

| 文档 | 说明 |
|---|---|
| [快速开始](docs/getting-started.md) | 本地环境、启动、默认账号、验证脚本。 |
| [架构设计](docs/architecture.md) | 当前系统分层、数据流、核心模块和技术债。 |
| [前端结构与交互逻辑](docs/frontend-structure.md) | Vue 页面、状态流转、API/WS 对接和演示页面。 |
| [多人房间与 AI DM 实时跑团](docs/multiplayer-realtime-design.md) | 多人房间设计与当前实现依据。 |
| [管理员后台说明](docs/admin-backend.md) | 管理员接口、前端后台、统计数据来源。 |
| [模块检查报告](docs/module-audit.md) | 按验收项梳理当前实现状态、验证脚本和后续风险。 |
| [答辩 PPT 生成指导](docs/defense-ppt-generation-guide.md) | 可交给其他 AI 的 PPT 生成说明。 |

## 推荐验证

后端静态与服务层验证：

```powershell
.venv\Scripts\python.exe -m compileall -q backend/app backend/scripts scripts
.venv\Scripts\python.exe -m backend.scripts.test_room_flow
.venv\Scripts\python.exe -m backend.scripts.test_admin_api
.venv\Scripts\python.exe -m backend.scripts.test_frontend_contract
```

多人端到端验证（可自动拉起服务）：

```powershell
.venv\Scripts\python.exe -m backend.scripts.e2e_multiplayer_api --spawn-server
```

前端构建：

```powershell
cd frontend
npm.cmd run build
```

## 许可证

本项目采用 [MIT License](LICENSE)。

# StoryForge

## 最新进度（2026-07-08）

- 前端主流程已接入后端基础接口：登录/注册、世界观、角色、会话、档案读取等。
- 顶部导航文字已按当前设计要求移除；大厅下方仍保留历史档案入口。
- 登录注册页已调整选项布局，并导出静态预览文件：`frontend/login-register-standalone.html`。
- 后端新增管理员后台能力：世界观/模组管理、会话记录管理、用户管理、系统操作日志。
- 数据库新增 `world_modules`、`admin_operation_logs`，`users` 增加 `email`、`status`。
- 管理员接口统一挂载在 `/api/v1/admin`，详细说明见 [管理员后台后端说明](docs/admin-backend.md)。

> AI 叙事、d20 规则判定与会话持久化结合的轻量单人跑团 Web 平台。

StoryForge 当前方向已从通用故事创作工具，收敛为“灵境档案”式 AI 跑团互动系统。MVP 目标是打通“选择世界观 -> 创建角色 -> AI 开局 -> 玩家行动 -> 后端掷骰判定 -> AI 推进剧情 -> 本局总结”的完整闭环。

## 当前状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端 API | 已实现主闭环 | FastAPI 路由包含世界观、角色、会话、行动、报告、故事/章节/设定/导出 |
| AI 模块 | 已实现 | Opening、ActionParser、Narrative、Critic、RevisionLoop、Summary，支持无 Key mock 兜底 |
| 数据库 | 已实现 | SQLAlchemy ORM 与 SQLite DDL 覆盖 12 张表，包含 Fact、NPC Profile、AI Review |
| D&D 5e 规则 | 已接入 | `rules/dnd5e/*.json` 提供属性、技能、职业、种族、背景等静态规则 |
| 前端 | 静态原型 | Vue 3 + Vite 页面已存在，暂未接入 Router、Pinia 与后端 API |
| 认证 | 已实现 MVP | 注册、登录、`/auth/me` 与 Bearer token 可用；无 token 时保留 demo 回退 |

## 功能规划

### P0

- [x] 世界观列表与选择
- [x] 基础角色创建与查询接口
- [x] AI 开局剧情生成
- [x] 玩家行动解析、d20 判定与剧情推进
- [x] 消息、判定、线索、任务、Fact、AI Review 持久化
- [x] 本局总结报告生成
- [ ] 前端与后端 API 联调
- [x] MVP 登录/注册与 Bearer token
- [x] D&D 5e 角色创建 MVP 规则校验

### P1

- [ ] 线索与任务面板
- [ ] 历史档案读取真实会话数据
- [ ] 报告页 ECharts 统计图表
- [ ] 管理端数据展示
- [ ] Opening Critic 审核

## 快速开始

详细步骤见 [docs/getting-started.md](docs/getting-started.md)。

```bash
git clone https://github.com/AOC2334/StoryForge.git
cd StoryForge

# 后端
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

本地地址：

- 后端健康检查：http://localhost:8000/health
- API 文档：http://localhost:8000/docs
- 前端开发服务：http://localhost:5173

## 文档

| 文档 | 说明 |
|------|------|
| [项目总览](docs/StoryForge灵境档案：AI 跑团互动与推理系统 (1).md) | 产品方向、导航与技术栈概览 |
| [实现规格书](docs/implementation-spec.md) | MVP 范围、API、DDL、业务流程、里程碑 |
| [架构设计](docs/architecture.md) | 当前架构、模块边界与依赖关系 |
| [模块检查报告](docs/module-audit.md) | 按现有文件结构检查各模块实现状态与风险 |
| [AI 模块设计](docs/ai-module-design.md) | Agent 架构、Fact 分层、接口规格 |
| [AI 模块实现说明](docs/ai-module-implementation.md) | Agent 实现、DB 交互、API、测试指南 |
| [D&D 5e 规则整合](docs/dnd5e-integration.md) | SRD 规则数据与角色创建流程 |
| [快速开始](docs/getting-started.md) | 环境准备与本地运行 |
| [开发指南](docs/development.md) | 分支、提交与代码规范 |
| [贡献指南](CONTRIBUTING.md) | 如何参与贡献 |
| [更新日志](CHANGELOG.md) | 版本变更记录 |

## 技术栈

| 层级 | 当前技术 |
|------|----------|
| 前端 | Vue 3 + Vite |
| 后端 | FastAPI + SQLAlchemy + Pydantic |
| 数据库 | SQLite（开发），MySQL 作为部署可选项 |
| AI | OpenAI 兼容 Chat Completions API，默认 DeepSeek 配置 |
| 规则数据 | D&D 5e SRD JSON |

## 项目结构

```text
StoryForge/
├── backend/              # FastAPI 后端、ORM、服务、AI 编排与验证脚本
├── frontend/             # Vue 3 + Vite 前端原型
├── rules/dnd5e/          # D&D 5e SRD 规则 JSON
├── scripts/              # 项目级脚本
├── docs/                 # 产品、架构、实现与模块检查文档
├── .env.example          # 根目录环境变量模板
├── backend.md            # 后端当前接口契约与进度
└── README.md
```

## 许可证

本项目采用 [MIT License](LICENSE) 开源。

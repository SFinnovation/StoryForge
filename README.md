# StoryForge 灵境档案

> AI 驱动的轻量化单人跑团平台 — 角色创建、 d20 判定、剧情推进、本局总结

StoryForge 面向跑团、互动小说与创意叙事场景，将 **AI 叙事**、**D&D 5e SRD 规则判定** 与 **会话持久化** 整合为完整 Web 体验。规则数据来自 Foundry VTT dnd5e 6.0.x（SRD 5.1），详见 [实现规格书](docs/implementation-spec.md) 与 [D&D 5e 整合说明](docs/dnd5e-integration.md)。

## 核心流程

```
选择世界观 → 创建角色 → AI 开局 → 玩家行动 → d20 判定 → AI 推进 → 本局总结
```

## 功能规划

### P0（MVP）

- [ ] 用户登录/注册
- [ ] 世界观选择与 **D&D 5e 角色创建**（种族/职业/背景/技能/属性雷达图）
- [ ] AI 开局剧情生成
- [ ] 跑团主界面（三栏：状态 / 对话 / 骰子与日志）
- [ ] 行动判定（d20 + 属性修正）
- [ ] 本局总结报告

### P1（加分）

- [ ] 线索与任务面板
- [ ] 历史档案
- [ ] ECharts 统计图表
- [ ] 管理端数据展示

## 快速开始

详细步骤见 [docs/getting-started.md](docs/getting-started.md)。

```bash
git clone https://github.com/AOC2334/StoryForge.git
cd StoryForge

# 复制环境变量模板
./scripts/setup-env.sh          # Windows: .\scripts\setup-env.ps1
# 编辑 .env，填写 LLM_API_KEY

# 后端（FastAPI）
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端（Vue 3）
cd frontend && npm install && npm run dev
```

> 后端与前端目录将在首轮开发中创建，启动命令以 [实现规格书](docs/implementation-spec.md#12-环境配置与本地启动) 为准。

## 文档

| 文档 | 说明 |
|------|------|
| [AI 模块设计](docs/ai-module-design.md) | **双 Agent 架构**、接口预留、Fact 分层 |
| [实现规格书](docs/implementation-spec.md) | API、DDL、里程碑 |
| [D&D 5e 规则整合](docs/dnd5e-integration.md) | SRD 规则数据与角色创建流程 |
| [架构设计](docs/architecture.md) | 系统分层与模块划分 |
| [快速开始](docs/getting-started.md) | 环境准备与本地运行 |
| [开发指南](docs/development.md) | 分支、提交与代码规范 |
| [贡献指南](CONTRIBUTING.md) | 如何参与贡献 |
| [更新日志](CHANGELOG.md) | 版本变更记录 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Pinia + Vue Router + ECharts |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | SQLite（开发）/ MySQL（可选） |
| AI | OpenAI 兼容 API（通义 / DeepSeek 等） |
| 认证 | JWT |

## 项目结构（目标态）

```
StoryForge/
├── frontend/             # Vue 3 前端
├── backend/              # FastAPI 后端
├── rules/dnd5e/          # D&D 5e SRD 规则 JSON（已提取）
├── scripts/              # 规则提取等工具脚本
├── docs/
│   ├── implementation-spec.md
│   └── architecture.md
├── README.md
└── .env.example
```

## 许可证

本项目采用 [MIT License](LICENSE) 开源。

## 联系方式

- Issue：[GitHub Issues](https://github.com/AOC2334/StoryForge/issues)

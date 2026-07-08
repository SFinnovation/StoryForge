# StoryForge

> 故事创作与管理的工具平台（项目初始化阶段）

StoryForge 旨在帮助创作者高效地构思、编写、组织与管理故事内容。本项目目前处于从零搭建阶段，文档与 Git 工作流已就绪，后续将逐步补充技术实现。

## 功能规划

- [ ] 故事项目管理（创建、编辑、归档）
- [ ] 章节与大纲编辑
- [ ] 角色与世界观设定
- [ ] 版本历史与导出

<<<<<<< HEAD
> 以上为初步规划，可根据实际需求调整。
=======
- [ ] 用户登录/注册
- [ ] 世界观选择与 **D&D 5e 角色创建**（种族/职业/背景/技能/属性雷达图）
- [x] AI 开局剧情生成（OpeningAgent）
- [ ] 跑团主界面（三栏：状态 / 对话 / 骰子与日志）
- [x] 行动判定（ActionParser + d20 + Narrative + Critic）
- [x] 本局总结报告（SummaryAgent）

### P1（加分）

- [ ] 线索与任务面板
- [ ] 历史档案
- [ ] ECharts 统计图表
- [ ] 管理端数据展示
>>>>>>> 38f0109237ad6b65c9edd640994015f91dcc4f4e

## 快速开始

详细步骤见 [docs/getting-started.md](docs/getting-started.md)。

```bash
# 克隆仓库
git clone https://github.com/AOC2334/StoryForge.git
cd StoryForge

# 后续：安装依赖、启动开发环境（待技术栈确定后补充）
```

## 文档

| 文档 | 说明 |
|------|------|
<<<<<<< HEAD
=======
| [AI 模块实现说明](docs/ai-module-implementation.md) | **五 Agent 实现**、DB 交互、API、测试指南 |
| [AI 模块设计](docs/ai-module-design.md) | 双 Agent 架构、Fact 分层、接口规格 |
| [实现规格书](docs/implementation-spec.md) | API、DDL、里程碑 |
| [D&D 5e 规则整合](docs/dnd5e-integration.md) | SRD 规则数据与角色创建流程 |
| [架构设计](docs/architecture.md) | 系统分层与模块划分 |
>>>>>>> 38f0109237ad6b65c9edd640994015f91dcc4f4e
| [快速开始](docs/getting-started.md) | 环境准备与本地运行 |
| [架构设计](docs/architecture.md) | 系统结构与模块划分 |
| [开发指南](docs/development.md) | 分支、提交与代码规范 |
| [贡献指南](CONTRIBUTING.md) | 如何参与贡献 |
| [更新日志](CHANGELOG.md) | 版本变更记录 |

## 技术栈

> 待确定。选定后请更新本节及 `docs/architecture.md`。

| 层级 | 技术 |
|------|------|
| 前端 | TBD |
| 后端 | TBD |
| 数据库 | TBD |
| 部署 | TBD |

## 项目结构

```
StoryForge/
├── docs/                 # 项目文档
├── .github/              # GitHub 模板与工作流（可选）
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
└── .gitattributes
```

## 许可证

本项目采用 [MIT License](LICENSE) 开源。

## 联系方式

- 维护者：TBD
- Issue：[GitHub Issues](https://github.com/AOC2334/StoryForge/issues)

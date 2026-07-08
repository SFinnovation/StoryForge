# 架构设计

> 本文档随项目演进持续更新。当前为初始骨架，技术选型确定后请填充具体内容。

## 概述

StoryForge 采用分层架构，将用户界面、业务逻辑与数据持久化解耦，便于独立开发与测试。

```
┌─────────────────────────────────────┐
│           客户端 / 前端              │
└─────────────────┬───────────────────┘
                  │ API
┌─────────────────▼───────────────────┐
│           应用服务层                 │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │ 故事管理 │ │ 章节编辑 │ │ 导出   │ │
│  └─────────┘ └─────────┘ └────────┘ │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│           数据持久层                 │
└─────────────────────────────────────┘
```

## 核心模块

### 1. 故事管理（Story）

- 创建、读取、更新、删除故事项目
- 元数据：标题、简介、标签、状态

### 2. 章节与大纲（Chapter / Outline）

- 树形大纲结构
- 章节正文编辑与排序

### 3. 设定库（Worldbuilding）

- 角色、地点、时间线等设定条目
- 与故事/章节的关联

### 4. 导出（Export）

- 支持 Markdown、PDF 等格式（待选型）

<<<<<<< HEAD
## 数据模型（草案）
=======
### 5. 行动判定（Action + Dice）

- AI 解析行动 → 映射 `skill_key`（如 `ste` 隐匿）
- **后端**执行 d20 + 属性修正 + 熟练加值
- 结果持久化到 `action_checks` 与 `messages`

### 6. 规则数据（Rules）

- `rules/dnd5e/`：从 Foundry dnd5e 包提取的 SRD JSON
- `rule_service` 加载并校验角色创建与检定

### 7. AI 编排（AI Service）— ✅ 已实现

双 Agent 架构：**Opening → ActionParser → RuleEngine → Narrative → Critic → RevisionLoop → StateCommitter → Summary**

| 文档 | 说明 |
|------|------|
| [ai-module-design.md](ai-module-design.md) | 架构设计、Fact 分层、接口规格 |
| [ai-module-implementation.md](ai-module-implementation.md) | **实现说明**：代码结构、DB 交互、API、测试 |

代码：`backend/app/ai/`（Agent）· `backend/app/services/`（编排）· `backend/scripts/verify_*.py`（验证）

### 8. 报告与可视化（Report + Admin）

- 结局报告落库 `reports`
- 管理端统计、ECharts 图表（P1）

## 数据模型（概要）
>>>>>>> 38f0109237ad6b65c9edd640994015f91dcc4f4e

```
Story
├── id
├── title
├── description
├── created_at / updated_at
└── chapters[] → Chapter
    ├── id
    ├── title
    ├── content
    ├── order
    └── parent_id (大纲层级)
```

## API 设计原则

- RESTful 或 RPC（待选型）
- 统一错误响应格式
- 分页、过滤、排序约定

## 非功能需求

| 项 | 目标 |
|----|------|
| 可测试性 | 核心业务逻辑与 I/O 分离 |
| 可扩展性 | 插件或模块边界清晰 |
| 安全性 | 敏感配置不入库、不提交 Git |

## 待决策项

- [ ] 前后端技术栈
- [ ] 数据库选型
- [ ] 认证与授权方案
- [ ] 部署与 CI/CD 平台

## 修订记录

| 日期 | 说明 |
|------|------|
<<<<<<< HEAD
=======
| 2026-07-08 | AI 模块 MVP 实现，补充实现说明文档链接 |
| 2026-07-07 | 对齐灵境档案跑团方向，替换原故事创作骨架 |
>>>>>>> 38f0109237ad6b65c9edd640994015f91dcc4f4e
| 2026-07-07 | 初始文档骨架 |

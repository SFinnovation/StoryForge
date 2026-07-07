# 架构设计

> 详细实现规格见 [implementation-spec.md](implementation-spec.md)。本文档描述系统分层与模块边界。

## 概述

StoryForge 灵境档案采用 **前后端分离** 架构，核心创新在于将 AI 叙事、规则化骰子判定与会话持久化结合，形成单人轻量跑团闭环。

```
┌─────────────────────────────────────────────────────────┐
│                    浏览器（Vue 3）                        │
│  登录 · 世界观 · 角色创建 · 跑团主界面 · 战报 · 管理端    │
└─────────────────────────┬───────────────────────────────┘
                          │ REST /api/v1
┌─────────────────────────▼───────────────────────────────┐
│                   FastAPI 应用层                          │
│  auth · worlds · characters · sessions · actions · admin │
└─────────────────────────┬───────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
  rule_service      dice_service       ai_service
  （属性/DC 校验）    （d20 掷骰）       （LLM 叙事）
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
              SQLite / MySQL（SQLAlchemy）
                          │
                          ▼
                  OpenAI 兼容 LLM API
```

## 核心模块

### 1. 用户与认证（Auth）

- JWT 登录/注册
- 角色：`user` / `admin`

### 2. 世界观（World）

- 内置剧本模板（奇幻、悬疑、赛博等）
- `opening_prompt` 供 AI 开局使用

### 3. 角色（Character）— D&D 5e

- 种族 / 职业 / 背景（`rules/dnd5e/*.json`）
- 六大属性、18 项技能熟练、豁免熟练
- 属性修正与熟练加值由 `rule_service` 计算

### 4. 跑团会话（Session）

- 状态机：`playing` → `finished` → `archived`
- 关联 world、character、messages、checks、clues、tasks

### 5. 行动判定（Action + Dice）

- AI 解析行动 → 映射 `skill_key`（如 `ste` 隐匿）
- **后端**执行 d20 + 属性修正 + 熟练加值
- 结果持久化到 `action_checks` 与 `messages`

### 6. 规则数据（Rules）

- `rules/dnd5e/`：从 Foundry dnd5e 包提取的 SRD JSON
- `rule_service` 加载并校验角色创建与检定

### 7. AI 编排（AI Service）

- 开局生成、行动理解、判定后叙事、本局总结
- 输出统一 JSON，Pydantic 校验

### 8. 报告与可视化（Report + Admin）

- 结局报告落库 `reports`
- 管理端统计、ECharts 图表（P1）

## 数据模型（概要）

```
User ──< Character
User ──< Session >── World
Session ──< Message
Session ──< ActionCheck
Session ──< Clue
Session ──< Task
Session ── Report
```

完整 DDL 见 [implementation-spec.md §6](implementation-spec.md#6-数据模型)。

## API 设计原则

- RESTful，`/api/v1` 前缀
- 统一响应：`{ code, message, data }`
- 骰子与规则逻辑 **不暴露给 AI**，仅后端执行
- 详细接口见 [implementation-spec.md §7](implementation-spec.md#7-api-规范)

## 非功能需求

| 项 | 目标 |
|----|------|
| 可测试性 | `dice_service`、`rule_service` 与 AI 调用解耦，可单测 |
| 可演示性 | 5 天内 P0 闭环可完整跑通 |
| 安全性 | LLM API Key 仅在后端 `.env`，不入库、不提交 Git |
| 可靠性 | AI 失败时有兜底叙事，不阻断会话 |

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-07 | 对齐灵境档案跑团方向，替换原故事创作骨架 |
| 2026-07-07 | 初始文档骨架 |

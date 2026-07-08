# StoryForge 灵境档案：AI 跑团互动与推理系统

> 本文档已重构为 **实现规格书**，完整内容见：  
> **[docs/implementation-spec.md](docs/implementation-spec.md)**

---

## 快速导航

| 章节 | 内容 |
|------|------|
| [项目定位与边界](docs/implementation-spec.md#1-项目定位与边界) | 做什么 / 不做什么 |
| [MVP 范围 P0/P1/P2](docs/implementation-spec.md#3-mvp-范围与验收标准) | 优先级与验收标准 |
| [数据模型 DDL](docs/implementation-spec.md#6-数据模型) | 可直接建表的 SQL |
| [API 规范](docs/implementation-spec.md#7-api-规范) | 请求/响应/错误码 |
| [AI 模块规范](docs/implementation-spec.md#9-ai-模块规范) | JSON Schema + Prompt 组织 |
| [五天里程碑](docs/implementation-spec.md#13-五天开发里程碑) | 按天拆分任务 |

---

## 核心闭环（一览）

```
选择世界观 → 创建角色 → AI 开局
    → 玩家行动 → d20 判定 → AI 推进剧情
    → 日志/线索 → 本局总结
```

## 技术栈

Vue 3 + FastAPI + SQLite + OpenAI 兼容 LLM API

## 一句话

StoryForge 是 **AI 叙事 + d20 规则判定 + 会话持久化** 的轻量化单人跑团 Web 平台，不是普通聊天机器人。

# StoryForge 数据库存储结构 · 交付说明

依据仓库 `docs/implementation-spec.md` §6（数据模型）与 §13 分工（数据/可视化：DDL、种子数据）完成，并与 `rules/dnd5e/*.json` 规则数据做了键值对齐验证。

## 交付物

| 文件 | 说明 |
|------|------|
| `schema.sql` | 9 张表 + 6 个索引的完整建表脚本（SQLite 友好，可迁移 MySQL） |
| `seed.sql` | 种子数据：admin 账号（哈希占位）+ 2 个世界观（奇幻遗迹 / 古堡悬疑） |
| `init_and_verify.py` | 一键建库 + 14 项自动校验（约束生效、规则键对齐、结构完整） |
| `storyforge.db` | 已建好并含样例数据的数据库，可直接用于联调演示 |

## 设计要点

数据库只存动态数据（用户、角色、会话、消息、判定、线索、任务、报告）；静态 D&D 5e 规则留在 `rules/dnd5e/*.json`，由后端规则引擎读取。两者通过字符串键衔接：`characters.race_id/class_id/background_id` 对应规则 JSON 的 `id`，`skills_json` 与 `action_checks.skill_key` 使用 `skills.json` 的技能键（如 `ste`），`attribute_used` 与 `saving_throws_json` 使用 `abilities.json` 的 `key`（如 `dexterity`）。

在规格书 DDL 基础上补充了三类保护（均为 SQLite/MySQL 兼容写法）：枚举字段 CHECK（role/status/message_type/importance/ending_type 等）、数值范围 CHECK（属性 1–30、等级 1–20、DC 5–30、骰值 1–20，对应规则引擎"AI 建议 DC 后钳制到 [5,30]"的约定）、JSON 列 `json_valid()` 校验。`reports.session_id` 加 UNIQUE 实现与会话的一对一。索引在规格书 3 个的基础上，为线索/任务面板和"我的角色"列表补了 3 个常用查询路径索引。

## 使用方式

```bash
python init_and_verify.py <rules/dnd5e 目录> <输出 db 路径>
```

## 遗留事项

- admin 的 `password_hash` 是占位符，需由 `backend/app/db/init_data.py` 从 `.env` 读取密码并以 bcrypt 写入。
- `backgrounds.json` 目前只有 acolyte 一个背景，角色创建页可先只放这一项，后续扩充规则数据无需改表。
- 部署 MySQL 时将 `AUTOINCREMENT` 改为 `AUTO_INCREMENT`、`DATETIME DEFAULT CURRENT_TIMESTAMP` 语义一致，其余 DDL 可直接复用；建议交由 Alembic 迁移管理。

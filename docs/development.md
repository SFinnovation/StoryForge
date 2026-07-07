# 开发指南

本文档约定 StoryForge 的日常开发流程与代码规范。

## 分支策略

采用简化的 Git Flow：

| 分支 | 用途 |
|------|------|
| `main` | 稳定可发布版本 |
| `develop` | 集成开发分支（可选，小团队可直接在 feature 合并到 main） |
| `feature/*` | 新功能 |
| `fix/*` | Bug 修复 |
| `docs/*` | 纯文档变更 |

### 分支命名示例

```
feature/story-crud
fix/chapter-order-bug
docs/update-readme
```

## 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 风格：

```
<type>(<scope>): <subject>

[optional body]
```

### Type 类型

| type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档 |
| `style` | 格式（不影响逻辑） |
| `refactor` | 重构 |
| `test` | 测试 |
| `chore` | 构建、依赖、工具链 |

### 示例

```
feat(story): add create story API
fix(chapter): correct sort order on drag
docs: update getting-started guide
```

## 开发流程

1. 从 `main`（或 `develop`）拉取最新代码
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 小步提交，保持每次提交可理解、可回滚
4. 本地自测通过后推送并发起 Pull Request
5. 至少一人 Review 后合并

## 代码规范

> 技术栈确定后，在此补充 linter、formatter 配置与命令。

通用原则：

- 保持函数/模块职责单一
- 避免无说明的魔法数字与硬编码密钥
- 新增公共 API 需有文档或注释说明用途
- 删除代码优先于大量注释掉的无用代码

## 环境变量

- 敏感配置放在 `.env`，模板见根目录 `.env.example` 与 `frontend/.env.example`
- 一键复制：`./scripts/setup-env.sh`（Windows：`.\scripts\setup-env.ps1`）
- **必填**：`LLM_API_KEY`（大模型）、生产环境的 `SECRET_KEY`
- 禁止将 `.env`、密钥、证书提交到 Git
- 详细说明见 [快速开始 — 环境变量配置](getting-started.md#环境变量配置)

## 本地 Git 建议（Windows）

```bash
git config core.autocrlf input
```

与仓库 `.gitattributes`（`eol=lf`）配合，减少行尾 diff 噪音。

## Pull Request 检查清单

- [ ] 分支基于最新的目标分支
- [ ] 提交信息清晰，符合规范
- [ ] 无调试代码、无意外提交的配置文件
- [ ] 相关文档已更新（若行为有变）
- [ ] 本地构建/测试通过（有测试后补充）

## 相关文档

- [快速开始](getting-started.md)
- [架构设计](architecture.md)
- [贡献指南](../CONTRIBUTING.md)

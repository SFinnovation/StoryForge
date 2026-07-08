# Changelog

本文件记录 StoryForge 的版本变更，格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added

- 管理员后台后端接口：世界观/模组管理、会话记录管理、用户管理、系统操作日志。
- 新增 `world_modules`、`admin_operation_logs` 表，`users` 表补充 `email` 与 `status` 字段。
- 新增管理员接口验证脚本 `backend/scripts/test_admin_api.py`。
- 新增登录注册页静态导出文件 `frontend/login-register-standalone.html`，便于外部调整视觉稿。
- 新增 [管理员后台后端说明](docs/admin-backend.md)。

### Changed

- 登录注册页移除“继续上次冒险”选项，并调整选项区布局。
- 前端顶部导航文字入口按当前设计要求移除，保留大厅下方历史档案入口。
- 被封禁用户登录和带 token 的普通接口访问会被后端拦截。

### Verified

- `.venv\Scripts\python.exe -m backend.scripts.test_admin_api`
- `.venv\Scripts\python.exe -m backend.scripts.test_frontend_contract`
- `.venv\Scripts\python.exe -m compileall backend`

### Added

- 初始化项目文档结构（README、docs/）
- Git 配置（`.gitignore`、`.gitattributes`）
- 贡献指南与更新日志

## [0.1.0] - 2026-07-07

### Added

- 项目骨架与文档初版

[Unreleased]: https://github.com/AOC2334/StoryForge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/AOC2334/StoryForge/releases/tag/v0.1.0

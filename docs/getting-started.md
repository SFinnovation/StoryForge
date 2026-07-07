# 快速开始

本文档说明如何在本地克隆并准备 StoryForge 开发环境。

## 前置要求

> 技术栈确定后，请补充具体版本要求。

- Git 2.30+
- （待补充）运行时 / 包管理器

## 克隆仓库

```bash
git clone https://github.com/AOC2334/StoryForge.git
cd StoryForge
```

## 环境配置

1. 复制环境变量模板（若存在）：

   ```bash
   cp .env.example .env
   ```

2. 按需修改 `.env` 中的配置项。

> `.env` 已被 `.gitignore` 忽略，请勿将密钥提交到仓库。

## 安装与运行

技术栈确定后，在此补充安装依赖与启动命令，例如：

```bash
# 示例（请替换为实际命令）
# npm install && npm run dev
# go run ./cmd/server
# docker compose up
```

## 验证

启动成功后，访问本地地址并确认服务正常响应（具体地址待补充）。

## 常见问题

### 行尾符差异导致大量 diff

仓库已通过 `.gitattributes` 统一使用 LF。Windows 用户建议：

```bash
git config core.autocrlf input
```

### 提交前检查

```bash
git status
git diff
```

确保未意外提交 `.env`、构建产物或 IDE 配置文件。

## 下一步

- 阅读 [开发指南](development.md) 了解分支与提交规范
- 阅读 [架构设计](architecture.md) 了解模块划分

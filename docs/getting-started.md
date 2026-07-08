# 快速开始

本文档说明如何在本地准备并运行 StoryForge。当前后端主闭环已实现，前端仍是静态原型，联调层待补齐。

## 前置要求

- Git 2.30+
- Python 3.11+（后端）
- Node.js 20+ 与 npm（前端）

Windows 用户建议优先使用 `python`、`pip`、`npm.cmd` 这类可执行命令。若 PowerShell 拦截 `npm.ps1`，可改用：

```powershell
npm.cmd install
npm.cmd run dev
```

## 克隆仓库

```bash
git clone https://github.com/AOC2334/StoryForge.git
cd StoryForge
```

## 环境配置

复制根目录环境变量模板：

```bash
cp .env.example .env
```

PowerShell：

```powershell
Copy-Item .env.example .env
```

本地开发时可保持 `LLM_API_KEY` 为空，AI 模块会走 mock/fallback 响应，便于无密钥跑通闭环。接入真实模型时填写：

```env
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=deepseek-chat
```

## 后端安装与运行

从仓库根目录执行：

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

后端启动时会调用 `init_db()` 自动建表。默认 SQLite 文件为 `storyforge.db`；如果使用 `.env.example` 中的 `DATABASE_URL=sqlite:///./data/storyforge.db`，请确保 `data/` 目录存在。

验证：

```bash
curl http://localhost:8000/health
```

浏览器访问：

- http://localhost:8000/health
- http://localhost:8000/docs

## 前端安装与运行

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：http://localhost:5173

注意：当前 `package.json` 与 `package-lock.json` 版本不完全同步，`npm ci` 可能失败；在修复 lockfile 前请使用 `npm install`。

## 验证脚本

后端提供多组脚本，建议在安装依赖后从仓库根目录运行：

```bash
python -m backend.scripts.test_ai_module
python -m backend.scripts.verify_implementation_spec
python -m backend.scripts.verify_ai_db_interaction
python -m backend.scripts.test_action_api
python -m backend.scripts.test_frontend_contract
python -m backend.scripts.bench_ai_module
```

静态检查：

```bash
python -m compileall -q backend/app backend/scripts scripts
python -m json.tool rules/dnd5e/core.json
python -m json.tool rules/dnd5e/skills.json
```

## 常见问题

### `python` 命令不存在

安装 Python 并勾选 Add Python to PATH，或使用本机已有解释器的完整路径运行。

### PowerShell 禁止运行 `npm.ps1`

改用 `npm.cmd`：

```powershell
npm.cmd install
npm.cmd run build
```

### `npm ci` 提示 lockfile 不同步

当前前端依赖锁文件与 `package.json` 存在版本不一致。临时开发使用 `npm install`；正式修复时需要更新并提交 `frontend/package-lock.json`。

### 行尾符差异导致大量 diff

仓库通过 `.gitattributes` 统一使用 LF。Windows 用户建议：

```bash
git config core.autocrlf input
```

## 下一步

- 阅读 [架构设计](architecture.md) 了解模块边界
- 阅读 [模块检查报告](module-audit.md) 查看当前风险
- 阅读 [实现规格书](implementation-spec.md) 对齐目标态需求

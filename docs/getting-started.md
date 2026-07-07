# 快速开始

本文档说明如何在本地克隆并配置 StoryForge 开发环境。

## 前置要求

| 工具 | 版本建议 | 用途 |
|------|----------|------|
| Git | 2.30+ | 版本管理 |
| Node.js | 18+ | 前端（Vue 3 + Vite） |
| npm / pnpm | 随 Node | 前端依赖 |
| Python | 3.11+ | 后端（FastAPI） |
| pip | 最新 | Python 依赖 |

可选：

- **PyYAML**：运行 `python scripts/extract_dnd5e_rules.py` 重新提取 D&D 规则时需要

## 克隆仓库

```bash
git clone https://github.com/AOC2334/StoryForge.git
cd StoryForge
```

## 环境变量配置

项目采用 **根目录 `.env`（后端）+ `frontend/.env`（前端）** 分离配置。

### 一键复制（推荐）

**macOS / Linux：**

```bash
chmod +x scripts/setup-env.sh
./scripts/setup-env.sh
```

**Windows PowerShell：**

```powershell
.\scripts\setup-env.ps1
```

### 手动复制

**macOS / Linux：**

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

**Windows PowerShell：**

```powershell
Copy-Item .env.example .env
Copy-Item frontend\.env.example frontend\.env
```

### 必须填写的项

打开根目录 `.env`，至少配置：

| 变量 | 说明 |
|------|------|
| `SECRET_KEY` | JWT 签名密钥，开发可用默认值，**生产必须更换** |
| `LLM_API_KEY` | 大模型 API 密钥（**团队开发核心配置**） |

`LLM_API_KEY` 可向项目负责人索取；或自行申请后填入。常用提供商预设已写在 `.env.example` 注释中。

### 大模型提供商速查

| 提供商 | `LLM_PROVIDER` | `LLM_API_BASE` | 推荐模型 |
|--------|----------------|----------------|----------|
| DeepSeek | `deepseek` | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `openai` | `https://api.openai.com/v1` | `gpt-4o-mini` |
| 通义千问 | `dashscope` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| 智谱 GLM | `zhipu` | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| Moonshot | `moonshot` | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |

切换提供商：修改 `.env` 中 `LLM_PROVIDER`、`LLM_API_BASE`、`LLM_API_KEY`、`LLM_MODEL` 四项即可。

### 环境变量文件说明

| 文件 | 作用 |
|------|------|
| `.env.example` | 后端完整模板（提交到 Git） |
| `.env` | 后端本地配置（**不提交**） |
| `frontend/.env.example` | 前端 Vite 模板 |
| `frontend/.env` | 前端本地配置（**不提交**） |
| `backend/.env.example` | 后端目录启动时的备用模板 |

> `.env` 已被 `.gitignore` 忽略。切勿将含真实密钥的文件提交到仓库。

### 生成 SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 安装与运行

> 后端与前端目录在首轮开发中创建；以下为规格书中的目标启动方式。

### 后端（FastAPI）

```bash
cd backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

若从 `backend/` 目录启动且使用根目录 `.env`，需确保加载路径正确；或复制 `backend/.env.example` 为 `backend/.env`（其中 `RULES_DIR=../rules/dnd5e`）。

### 前端（Vue 3）

```bash
cd frontend
npm install
npm run dev
```

默认访问：http://localhost:5173

## 验证

| 检查项 | 地址 / 命令 |
|--------|-------------|
| 后端健康 | http://localhost:8000/docs （Swagger） |
| 前端页面 | http://localhost:5173 |
| API 联通 | 前端 `.env` 中 `VITE_API_BASE_URL` 指向 `http://localhost:8000/api/v1` |
| 数据库 | 首次启动后生成 `backend/data/storyforge.db`（SQLite） |

## 演示账号（开发种子数据）

当 `SEED_DEMO_DATA=true` 时，默认创建：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `admin` | `admin123` |
| 演示用户 | `demo` | `demo123` |

生产环境请关闭 `SEED_DEMO_DATA` 并修改 `ADMIN_PASSWORD`。

## 常见问题

### 行尾符差异导致大量 diff

仓库已通过 `.gitattributes` 统一使用 LF。Windows 用户建议：

```bash
git config core.autocrlf input
```

### CORS 报错

确认根目录 `.env` 中 `CORS_ORIGINS` 包含前端地址（默认 `http://localhost:5173`）。

### AI 接口超时

调大 `.env` 中 `LLM_TIMEOUT`（建议 60）及 `frontend/.env` 中 `VITE_HTTP_TIMEOUT`（建议 90000）。

### 提交前检查

```bash
git status
git diff
```

确保未意外提交 `.env`、构建产物或 IDE 配置文件。

## 下一步

- [开发指南](development.md) — 分支与提交规范
- [实现规格书](implementation-spec.md) — API 与模块说明
- [D&D 5e 规则整合](dnd5e-integration.md) — 规则数据说明

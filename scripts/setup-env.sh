#!/usr/bin/env bash
# 复制环境变量模板，供组内成员本地开发使用
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

copy_if_missing() {
  local src="$1"
  local dest="$2"
  if [[ -f "$dest" ]]; then
    echo "[skip] 已存在: $dest"
  else
    cp "$src" "$dest"
    echo "[ok]   已创建: $dest"
  fi
}

copy_if_missing ".env.example" ".env"
copy_if_missing "frontend/.env.example" "frontend/.env"

echo ""
echo "环境模板已就绪。请编辑以下文件并填写 LLM_API_KEY："
echo "  - $ROOT/.env"
echo "  - $ROOT/frontend/.env （一般无需修改，除非改 API 地址）"
echo ""
echo "生成 SECRET_KEY："
echo "  python -c \"import secrets; print(secrets.token_urlsafe(32))\""

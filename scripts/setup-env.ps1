# 复制环境变量模板，供组内成员本地开发使用
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Copy-IfMissing {
    param([string]$Src, [string]$Dest)
    if (Test-Path $Dest) {
        Write-Host "[skip] exists: $Dest"
    } else {
        Copy-Item $Src $Dest
        Write-Host "[ok]   created: $Dest"
    }
}

Copy-IfMissing ".env.example" ".env"
Copy-IfMissing "frontend\.env.example" "frontend\.env"

Write-Host ""
Write-Host "Done. Edit .env and set LLM_API_KEY before starting the backend."
Write-Host "See docs/getting-started.md for provider presets and SECRET_KEY generation."

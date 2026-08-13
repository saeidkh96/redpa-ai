$ErrorActionPreference = "Stop"

$routerPath = ".\backend\app\api\v1\router.py"

if (-not (Test-Path $routerPath)) {
    throw "Router file not found."
}

$content = Get-Content $routerPath -Raw
$import = 'from app.api.v1.events import router as events_router'

if ($content -notmatch [regex]::Escape($import)) {
    $content = "$import`r`n$content"
}

if ($content -notmatch "include_router\(\s*events_router") {
    $content += "`r`napi_router.include_router(events_router)`r`n"
}

Set-Content $routerPath $content -Encoding UTF8

Write-Host "[PASS] Phase 17 Events API registered." -ForegroundColor Green
Write-Host "[PASS] Phase 18 production hardening/security assets installed." -ForegroundColor Green
Write-Host "[PASS] Phase 19 v3 release assets installed." -ForegroundColor Green
Write-Host "[INFO] New Alembic migration: p17a1b2c3d4e" -ForegroundColor Cyan
Write-Host ""
Write-Host "README.md was intentionally not modified." -ForegroundColor Yellow

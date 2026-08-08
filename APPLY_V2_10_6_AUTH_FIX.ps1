$ErrorActionPreference = "Stop"

$cssPath = ".\frontend\app\globals.css"
$patchPath = ".\CSS_APPEND.txt"
$marker = "RedPA v2 Phase 10.6 - authenticated MCP console"

if (-not (Test-Path $cssPath)) {
    throw "frontend/app/globals.css was not found."
}

if (-not (Test-Path $patchPath)) {
    throw "CSS_APPEND.txt was not found."
}

$css = Get-Content $cssPath -Raw

if ($css -notmatch [regex]::Escape($marker)) {
    Add-Content -Path $cssPath -Value ("`r`n" + (Get-Content $patchPath -Raw))
}

Write-Host "[PASS] MCP authentication patch applied." -ForegroundColor Green
Write-Host ""
Write-Host "Rebuild frontend:" -ForegroundColor Cyan
Write-Host "docker compose up -d --build --force-recreate frontend"

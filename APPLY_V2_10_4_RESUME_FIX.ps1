$ErrorActionPreference = "Stop"

$cssPath = ".\frontend\app\globals.css"
$patchPath = ".\CSS_APPEND.txt"
$marker = "RedPA v2 Phase 10.4 - resumed workflow state"

if (-not (Test-Path $cssPath)) {
    throw "frontend/app/globals.css was not found."
}

if (-not (Test-Path $patchPath)) {
    throw "CSS_APPEND.txt was not found."
}

$css = Get-Content $cssPath -Raw

if ($css -notmatch [regex]::Escape($marker)) {
    $append = Get-Content $patchPath -Raw
    Add-Content -Path $cssPath -Value ("`r`n" + $append)
    Write-Host "[PASS] Resume-state CSS added." -ForegroundColor Green
}
else {
    Write-Host "[PASS] Resume-state CSS already exists." -ForegroundColor Green
}

Write-Host ""
Write-Host "Rebuild frontend:" -ForegroundColor Cyan
Write-Host "docker compose up -d --build --force-recreate frontend"

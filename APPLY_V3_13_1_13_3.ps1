$ErrorActionPreference = "Stop"

$routerPath = ".\backend\app\api\v1\router.py"

if (-not (Test-Path $routerPath)) {
    throw "Router file not found: $routerPath"
}

$content = Get-Content $routerPath -Raw

if ($content -notmatch "guardrails_router") {
    $import = "from app.api.v1.guardrails import router as guardrails_router"

    if ($content -match "from fastapi import APIRouter") {
        $content = $content -replace `
            "from fastapi import APIRouter", `
            "$import`r`nfrom fastapi import APIRouter"
    }
    else {
        $content = "$import`r`n$content"
    }
}

if ($content -notmatch "include_router\(\s*guardrails_router") {
    $content += "`r`napi_router.include_router(guardrails_router)`r`n"
}

Set-Content $routerPath $content -Encoding UTF8

Write-Host "[PASS] Guardrails API router registered." -ForegroundColor Green
Write-Host ""
Write-Host "Phase 13 uses docker-compose.phase13.yml as a Compose override." -ForegroundColor Cyan
Write-Host "Use both files when starting Phase 13 services:" -ForegroundColor Cyan
Write-Host 'docker compose -f docker-compose.yml -f docker-compose.phase13.yml up -d --build policy-service backend' -ForegroundColor Yellow

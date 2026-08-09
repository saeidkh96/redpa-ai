$ErrorActionPreference = "Stop"

$routerPath = ".\backend\app\api\v1\router.py"

if (-not (Test-Path $routerPath)) {
    throw "Router file not found: $routerPath"
}

$content = Get-Content $routerPath -Raw

if ($content -notmatch "policy_enforcement_router") {
    $import = "from app.api.v1.policy_enforcement import router as policy_enforcement_router"

    if ($content -match "from fastapi import APIRouter") {
        $content = $content -replace `
            "from fastapi import APIRouter", `
            "$import`r`nfrom fastapi import APIRouter"
    }
    else {
        $content = "$import`r`n$content"
    }
}

if ($content -notmatch "include_router\(\s*policy_enforcement_router") {
    $content += "`r`napi_router.include_router(policy_enforcement_router)`r`n"
}

Set-Content $routerPath $content -Encoding UTF8

Write-Host "[PASS] Policy enforcement API router registered." -ForegroundColor Green
Write-Host "[INFO] New Alembic migration: f13a4b5c6d7e" -ForegroundColor Cyan

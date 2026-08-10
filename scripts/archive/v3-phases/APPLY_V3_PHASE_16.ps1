$ErrorActionPreference = "Stop"

$routerPath = ".\backend\app\api\v1\router.py"

if (-not (Test-Path $routerPath)) {
    throw "Router file not found."
}

$content = Get-Content $routerPath -Raw

$imports = @(
    'from app.api.v1.tenants import router as tenants_router',
    'from app.api.v1.oauth import router as oauth_router'
)

foreach ($import in $imports) {
    if ($content -notmatch [regex]::Escape($import)) {
        $content = "$import`r`n$content"
    }
}

if ($content -notmatch "include_router\(\s*tenants_router") {
    $content += "`r`napi_router.include_router(tenants_router)`r`n"
}

if ($content -notmatch "include_router\(\s*oauth_router") {
    $content += "`r`napi_router.include_router(oauth_router)`r`n"
}

Set-Content $routerPath $content -Encoding UTF8

Write-Host "[PASS] Tenant API router registered." -ForegroundColor Green
Write-Host "[PASS] OAuth API router registered." -ForegroundColor Green
Write-Host "[INFO] New Alembic migration: p16a1b2c3d4e" -ForegroundColor Cyan
Write-Host "[INFO] OAuth callback remains intentionally non-production until real provider credentials + server-side state persistence are configured." -ForegroundColor Yellow

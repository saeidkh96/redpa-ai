$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 16 Final Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/security/rbac.py",
    "backend/app/security/tenant_context.py",
    "backend/app/models/tenant.py",
    "backend/app/models/oauth_identity.py",
    "backend/app/services/tenant_service.py",
    "backend/app/services/authorization_service.py",
    "backend/app/auth/oauth.py",
    "backend/app/auth/oauth_providers.py",
    "backend/app/api/v1/tenants.py",
    "backend/app/api/v1/oauth.py",
    "backend/alembic/versions/p16a1b2c3d4e_create_tenants_and_oauth.py",
    "frontend/components/AccessControlCenter.tsx",
    "frontend/app/access/page.tsx"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 16 file: $path"
    }
}
Pass "Phase 16 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}
Pass "Python compilation"

python -m pytest `
    .\tests\test_phase16_rbac.py `
    .\tests\test_phase16_tenant_scope.py `
    .\tests\test_phase16_oauth.py `
    .\tests\test_phase16_api_contract.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 16 tests failed."
}
Pass "RBAC / tenancy / OAuth tests"

python -m pytest tests -q
if ($LASTEXITCODE -ne 0) {
    throw "Full regression suite failed."
}
Pass "Full regression suite"

Push-Location backend
try {
    $heads = alembic heads
    if ($LASTEXITCODE -ne 0) {
        throw "alembic heads failed."
    }

    if ($heads -notmatch "p16a1b2c3d4e") {
        throw "Expected Alembic head p16a1b2c3d4e. Got: $heads"
    }
}
finally {
    Pop-Location
}
Pass "Phase 16 Alembic head"

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    config | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose config failed."
}
Pass "Docker Compose config"

$routerContent = Get-Content ".\backend\app\api\v1\router.py" -Raw
if ($routerContent -notmatch "tenants_router") {
    throw "Tenant router is not registered. Run APPLY."
}
if ($routerContent -notmatch "oauth_router") {
    throw "OAuth router is not registered. Run APPLY."
}
Pass "API router registration"

Write-Host ""
Write-Host "Phase 16 source verification passed." -ForegroundColor Green
Write-Host "Next: apply migration in the Docker backend, rebuild backend/frontend, then run runtime smoke tests." -ForegroundColor Cyan

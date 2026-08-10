$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 13.4 / 13.5 / 13.6 Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/services/policy_enforcement_service.py",
    "backend/app/services/guarded_execution_service.py",
    "backend/app/services/policy_audit_service.py",
    "backend/app/models/policy_audit_event.py",
    "backend/app/monitoring/policy_metrics.py",
    "backend/app/api/v1/policy_enforcement.py",
    "backend/alembic/versions/f13a4b5c6d7e_create_policy_audit_events.py"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 13.4-13.6 file: $path"
    }
}
Pass "Phase 13.4-13.6 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}
Pass "Python compilation"

python -m pytest `
    .\tests\test_policy_enforcement_service.py `
    .\tests\test_guarded_execution_service.py `
    .\tests\test_policy_api_contract.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 13.4-13.6 tests failed."
}
Pass "Policy enforcement tests"

$routerContent = Get-Content ".\backend\app\api\v1\router.py" -Raw
if ($routerContent -notmatch "policy_enforcement_router") {
    throw "Policy enforcement router is not registered. Run APPLY first."
}
Pass "Policy enforcement API registration"

Push-Location backend
try {
    $heads = alembic heads
    if ($LASTEXITCODE -ne 0) {
        throw "alembic heads failed."
    }

    if ($heads -notmatch "f13a4b5c6d7e") {
        throw "Expected Alembic head f13a4b5c6d7e was not found. Heads: $heads"
    }
}
finally {
    Pop-Location
}
Pass "Policy audit Alembic head"

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    config | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Phase 13 Docker Compose config failed."
}
Pass "Phase 13 Docker Compose config"

Write-Host ""
Write-Host "Phase 13.4 / 13.5 / 13.6 verification passed." -ForegroundColor Green
Write-Host "Human Review bridge + guarded tool/MCP boundary + persistent policy audit/metrics are ready." -ForegroundColor Green
Write-Host ""
Write-Host "Next: apply Alembic migration, rebuild backend, then smoke-test /api/v1/policy endpoints." -ForegroundColor Cyan

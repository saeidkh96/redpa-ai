$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phases 17 / 18 / 19 Source Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/events/contracts.py",
    "backend/app/events/redis_stream_bus.py",
    "backend/app/models/event_outbox.py",
    "backend/app/services/event_outbox_service.py",
    "backend/app/services/event_publisher_service.py",
    "backend/app/api/v1/events.py",
    "backend/alembic/versions/p17a1b2c3d4e_create_event_outbox.py",
    "backend/app/security/production_guard.py",
    "scripts/security/secret_scan.py",
    "docs/security/THREAT_MODEL_V3.md",
    "deploy/kubernetes/network-policy-phase18.yaml",
    "frontend/app/events/page.tsx",
    "docs/release/V3_RELEASE_NOTES.md",
    "RELEASE_MANIFEST_v3.0.0.json",
    "scripts/release/build_v3_archive.py"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 17-19 file: $path"
    }
}
Pass "Phase 17-19 files"

python -m compileall -q backend/app scripts
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}
Pass "Python compilation"

python -m pytest `
    .\tests\test_phase17_events.py `
    .\tests\test_phase17_api_contract.py `
    .\tests\test_phase18_production_security.py `
    .\tests\test_phase18_secret_scan_contract.py `
    .\tests\test_phase19_release_contract.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17-19 focused tests failed."
}
Pass "Phase 17-19 focused tests"

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

    if ($heads -notmatch "p17a1b2c3d4e") {
        throw "Expected Alembic head p17a1b2c3d4e. Got: $heads"
    }
}
finally {
    Pop-Location
}
Pass "Phase 17 Alembic head"

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    config | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose config failed."
}
Pass "Docker Compose config"

$routerContent = Get-Content ".\backend\app\api\v1\router.py" -Raw
if ($routerContent -notmatch "events_router") {
    throw "Events router not registered. Run APPLY script."
}
Pass "Events API registration"

Write-Host ""
Write-Host "SOURCE VERIFICATION COMPLETE" -ForegroundColor Green
Write-Host "Next: migrate Docker DB, rebuild backend/frontend, then run runtime/final verification." -ForegroundColor Cyan

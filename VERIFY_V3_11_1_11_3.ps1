$ErrorActionPreference = "Stop"

function Pass($message) { Write-Host "[PASS] $message" -ForegroundColor Green }

Write-Host "RedPA AI v3 - Phase 11.1 / 11.2 / 11.3 Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/models/evaluation.py",
    "backend/app/schemas/evaluation.py",
    "backend/app/evaluation/__init__.py",
    "backend/app/evaluation/metrics.py",
    "backend/app/services/evaluation_service.py",
    "backend/alembic/versions/e11a1b2c3d4e_create_evaluation_tables.py",
    "tests/test_evaluation_metrics.py",
    "tests/test_evaluation_service.py"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) { throw "Missing required Phase 11 file: $path" }
}
Pass "Phase 11.1-11.3 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }
Pass "Python compilation"

python -m pytest .\tests\test_evaluation_metrics.py .\tests\test_evaluation_service.py -q
if ($LASTEXITCODE -ne 0) { throw "Phase 11 evaluation tests failed." }
Pass "Evaluation tests"

Push-Location backend
try {
    $heads = alembic heads
    if ($LASTEXITCODE -ne 0) { throw "alembic heads failed." }
    if ($heads -notmatch "e11a1b2c3d4e") { throw "Expected Phase 11 Alembic head e11a1b2c3d4e was not found." }
}
finally {
    Pop-Location
}
Pass "Alembic head"

Write-Host ""
Write-Host "Phase 11.1 / 11.2 / 11.3 verification passed." -ForegroundColor Green
Write-Host "Next: apply alembic upgrade head from backend, then run the full test suite." -ForegroundColor Cyan

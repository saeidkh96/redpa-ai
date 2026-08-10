$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 11.4 / 11.5 / 11.6 Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/evaluation/benchmark.py",
    "backend/app/schemas/benchmark.py",
    "backend/app/api/v1/evaluations.py",
    "frontend/components/EvaluationDashboard.tsx",
    "frontend/app/evaluations/page.tsx",
    "frontend/app/evaluations/layout.tsx",
    "tests/test_benchmark_engine.py",
    "tests/test_evaluation_api_schema.py"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing required Phase 11.4-11.6 file: $path"
    }
}
Pass "Phase 11.4-11.6 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}
Pass "Python compilation"

python -m pytest `
    .\tests\test_benchmark_engine.py `
    .\tests\test_evaluation_api_schema.py `
    .\tests\test_evaluation_metrics.py `
    .\tests\test_evaluation_service.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 11.4-11.6 tests failed."
}
Pass "Evaluation + benchmark tests"

$routerContent = Get-Content ".\backend\app\api\v1\router.py" -Raw
if ($routerContent -notmatch "evaluations\.router") {
    throw "Evaluation API router is not registered. Run scripts/archive/v3-phases/APPLY_V3_11_5_API.ps1 first."
}
Pass "Evaluation API registration"

docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "docker compose config failed."
}
Pass "Docker Compose config"

docker compose build frontend
if ($LASTEXITCODE -ne 0) {
    throw "Frontend production build failed."
}
Pass "Evaluation dashboard production build"

Write-Host ""
Write-Host "Phase 11.4 / 11.5 / 11.6 verification passed." -ForegroundColor Green
Write-Host "Next: rebuild/restart backend and frontend, then smoke-test /api/v1/evaluations and /evaluations." -ForegroundColor Cyan

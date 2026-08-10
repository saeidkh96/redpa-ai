$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 11 Final Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/models/evaluation.py",
    "backend/app/schemas/evaluation.py",
    "backend/app/schemas/benchmark.py",
    "backend/app/schemas/evaluation_observability.py",
    "backend/app/evaluation/metrics.py",
    "backend/app/evaluation/benchmark.py",
    "backend/app/evaluation/telemetry.py",
    "backend/app/services/evaluation_service.py",
    "backend/app/api/v1/evaluations.py",
    "frontend/components/EvaluationDashboard.tsx",
    "frontend/app/evaluations/page.tsx",
    "backend/alembic/versions/e11a1b2c3d4e_create_evaluation_tables.py"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 11 path: $path"
    }
}
Pass "Phase 11 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}
Pass "Python compilation"

python -m pytest .\tests -q
if ($LASTEXITCODE -ne 0) {
    throw "Full test suite failed."
}
Pass "Full test suite"

Push-Location backend
try {
    $heads = alembic heads
    if ($LASTEXITCODE -ne 0) {
        throw "alembic heads failed."
    }

    if ($heads -notmatch "e11a1b2c3d4e") {
        throw "Expected Phase 11 Alembic head e11a1b2c3d4e."
    }
}
finally {
    Pop-Location
}
Pass "Alembic head"

$containerCurrent = docker compose exec -T backend alembic current
if ($LASTEXITCODE -ne 0) {
    throw "Could not read container Alembic revision."
}

if ($containerCurrent -notmatch "e11a1b2c3d4e") {
    throw "Docker PostgreSQL is not migrated to Phase 11 head. Run: docker compose exec backend alembic upgrade head"
}
Pass "Docker database migration"

docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "docker compose config failed."
}
Pass "Docker Compose config"

$metrics = Invoke-RestMethod "http://localhost:8000/api/v1/evaluations/metrics"
if ($metrics.Count -ne 9) {
    throw "Expected 9 evaluation metrics, found $($metrics.Count)."
}
Pass "Evaluation metric catalog"

$observability = Invoke-RestMethod "http://localhost:8000/api/v1/evaluations/observability"
if ($null -eq $observability.runs) {
    throw "Evaluation observability payload is missing runs."
}
if ($null -eq $observability.benchmarks) {
    throw "Evaluation observability payload is missing benchmarks."
}
Pass "Evaluation observability API"

$prometheus = Invoke-WebRequest "http://localhost:8000/api/v1/metrics" -UseBasicParsing
if ($prometheus.StatusCode -ne 200) {
    throw "Prometheus metrics endpoint failed."
}

$metricText = $prometheus.Content
$requiredPrometheus = @(
    "redpa_evaluation_runs_total",
    "redpa_evaluation_metric_score",
    "redpa_evaluation_active_runs",
    "redpa_benchmark_runs_total"
)

foreach ($metricName in $requiredPrometheus) {
    if ($metricText -notmatch [regex]::Escape($metricName)) {
        throw "Prometheus evaluation metric missing: $metricName"
    }
}
Pass "Evaluation Prometheus telemetry"

$frontend = Invoke-WebRequest "http://localhost:3001/evaluations" -UseBasicParsing
if ($frontend.StatusCode -ne 200) {
    throw "Evaluation dashboard failed."
}
Pass "Evaluation dashboard HTTP 200"

docker compose build frontend
if ($LASTEXITCODE -ne 0) {
    throw "Frontend production build failed."
}
Pass "Frontend production build"

Write-Host ""
Write-Host "PHASE 11 COMPLETE" -ForegroundColor Green
Write-Host "Evaluation Core + Metrics + Service + Benchmarking + API + Dashboard + Observability + Tests are verified." -ForegroundColor Green
Write-Host "Next: Phase 12 - Multi-LLM Model Gateway." -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 12.4 / 12.5 / 12.6 Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/model_gateway/routing.py",
    "backend/app/model_gateway/reliability.py",
    "backend/app/model_gateway/gateway.py",
    "backend/app/model_gateway/bootstrap.py",
    "backend/app/schemas/model_gateway.py",
    "backend/app/api/v1/model_gateway.py",
    "tests/test_model_gateway_routing.py",
    "tests/test_model_gateway_reliability.py",
    "tests/test_model_gateway_gateway.py",
    "tests/test_model_gateway_api_schema.py"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 12.4-12.6 file: $path"
    }
}
Pass "Phase 12.4-12.6 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}
Pass "Python compilation"

python -m pytest `
    .\tests\test_model_gateway_contracts.py `
    .\tests\test_model_gateway_factory_registry.py `
    .\tests\test_model_gateway_adapters.py `
    .\tests\test_model_gateway_routing.py `
    .\tests\test_model_gateway_reliability.py `
    .\tests\test_model_gateway_gateway.py `
    .\tests\test_model_gateway_api_schema.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Model Gateway Phase 12 tests failed."
}
Pass "Model Gateway routing/reliability tests"

$routerContent = Get-Content ".\backend\app\api\v1\router.py" -Raw
if ($routerContent -notmatch "model_gateway\.router") {
    throw "Model Gateway API router is not registered. Run scripts/archive/v3-phases/APPLY_V3_12_6_API.ps1."
}
Pass "Model Gateway API registration"

Push-Location backend
try {
    python -c "from app.model_gateway.bootstrap import model_gateway; print([(d.name, d.default_model) for d in model_gateway.registry.descriptors()]); print(model_gateway.preview_route())"

    if ($LASTEXITCODE -ne 0) {
        throw "Model Gateway runtime bootstrap failed."
    }
}
finally {
    Pop-Location
}
Pass "Model Gateway runtime bootstrap"

Write-Host ""
Write-Host "Phase 12.4 / 12.5 / 12.6 verification passed." -ForegroundColor Green
Write-Host "Routing Strategy + Reliability + Model Gateway API are ready." -ForegroundColor Green
Write-Host "Next: rebuild backend and smoke-test authenticated /api/v1/model-gateway endpoints." -ForegroundColor Cyan

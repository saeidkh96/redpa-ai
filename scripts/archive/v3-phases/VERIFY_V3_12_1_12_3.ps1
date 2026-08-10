$ErrorActionPreference = "Stop"
function Pass($message) { Write-Host "[PASS] $message" -ForegroundColor Green }

Write-Host "RedPA AI v3 - Phase 12.1 / 12.2 / 12.3 Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/model_gateway/__init__.py",
    "backend/app/model_gateway/contracts.py",
    "backend/app/model_gateway/config.py",
    "backend/app/model_gateway/factory.py",
    "backend/app/model_gateway/registry.py",
    "backend/app/model_gateway/bootstrap.py",
    "backend/app/model_gateway/providers/ollama.py",
    "backend/app/model_gateway/providers/openai_compatible.py",
    "backend/app/model_gateway/providers/mock.py",
    "tests/test_model_gateway_contracts.py",
    "tests/test_model_gateway_factory_registry.py",
    "tests/test_model_gateway_adapters.py"
)
foreach ($path in $required) { if (-not (Test-Path $path)) { throw "Missing Phase 12 file: $path" } }
Pass "Phase 12.1-12.3 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }
Pass "Python compilation"

python -m pytest .\tests\test_model_gateway_contracts.py .\tests\test_model_gateway_factory_registry.py .\tests\test_model_gateway_adapters.py -q
if ($LASTEXITCODE -ne 0) { throw "Model Gateway tests failed." }
Pass "Model Gateway TDD tests"

Push-Location backend
try {
    python -c "from app.model_gateway.bootstrap import model_gateway_registry; print([d.name for d in model_gateway_registry.descriptors()])"

    if ($LASTEXITCODE -ne 0) {
        throw "Model Gateway bootstrap failed."
    }
}
finally {
    Pop-Location
}

Pass "Configuration-driven provider registry"
if ($LASTEXITCODE -ne 0) { throw "Model Gateway bootstrap failed." }
Pass "Configuration-driven provider registry"

Write-Host ""
Write-Host "Phase 12.1 / 12.2 / 12.3 verification passed." -ForegroundColor Green
Write-Host "SOLID provider contract + Adapter Pattern + Factory/Registry are ready." -ForegroundColor Green
Write-Host "Next: Phase 12.4 - Routing Strategy." -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 13.1 / 13.2 / 13.3 Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/guardrails/contracts.py",
    "backend/app/guardrails/client.py",
    "backend/app/guardrails/service.py",
    "backend/app/guardrails/tool_guard.py",
    "backend/app/api/v1/guardrails.py",
    "backend/app/schemas/guardrails.py",
    "policy-service/pom.xml",
    "policy-service/Dockerfile",
    "policy-service/src/main/java/ai/redpa/policy/PolicyServiceApplication.java",
    "policy-service/src/main/java/ai/redpa/policy/application/PolicyEngine.java",
    "policy-service/src/test/resources/features/policy_decisions.feature",
    "docker-compose.phase13.yml"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 13 file: $path"
    }
}
Pass "Phase 13.1-13.3 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}
Pass "Python compilation"

python -m pytest `
    .\tests\test_guardrail_contracts.py `
    .\tests\test_guardrail_client.py `
    .\tests\test_guardrail_service.py `
    .\tests\test_guardrail_api_contract.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Python guardrail tests failed."
}
Pass "Python guardrail tests"

$routerContent = Get-Content ".\backend\app\api\v1\router.py" -Raw
if ($routerContent -notmatch "guardrails_router") {
    throw "Guardrails API router is not registered. Run scripts/archive/v3-phases/APPLY_V3_13_1_13_3.ps1."
}
Pass "Guardrails API registration"

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    config | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Phase 13 Docker Compose config failed."
}
Pass "Phase 13 Docker Compose config"

Write-Host ""
Write-Host "Building and executing Spring Boot unit + BDD tests..." -ForegroundColor Cyan

docker build `
    --target test `
    -t redpa-policy-service-test `
    .\policy-service

if ($LASTEXITCODE -ne 0) {
    throw "Spring Boot / Cucumber tests failed."
}
Pass "Spring Boot unit + BDD tests"

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    build policy-service

if ($LASTEXITCODE -ne 0) {
    throw "Policy Service image build failed."
}
Pass "Policy Service production image"

Write-Host ""
Write-Host "Phase 13.1 / 13.2 / 13.3 verification passed." -ForegroundColor Green
Write-Host "Guardrail contracts + Spring Boot Policy Service + BDD rules are ready." -ForegroundColor Green
Write-Host ""
Write-Host "Next runtime step:" -ForegroundColor Cyan
Write-Host 'docker compose -f docker-compose.yml -f docker-compose.phase13.yml up -d --build policy-service backend' -ForegroundColor Yellow

$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 13.8 Security / Integration / BDD Verification" -ForegroundColor Cyan

python -m pytest `
    .\tests\test_policy_phase13_security.py `
    .\tests\test_policy_phase13_integration.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 13.8 Python tests failed."
}
Pass "Policy security/integration tests"

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    build policy-service

if ($LASTEXITCODE -ne 0) {
    throw "Policy Service build/tests failed."
}
Pass "Spring Boot JUnit/Cucumber build"

Write-Host ""
Write-Host "Phase 13.8 verification passed." -ForegroundColor Green

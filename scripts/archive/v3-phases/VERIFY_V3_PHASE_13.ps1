$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 13 Final Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/guardrails/contracts.py",
    "backend/app/guardrails/service.py",
    "backend/app/services/policy_enforcement_service.py",
    "backend/app/services/guarded_execution_service.py",
    "backend/app/services/policy_audit_service.py",
    "backend/app/models/policy_audit_event.py",
    "backend/app/monitoring/policy_metrics.py",
    "backend/app/api/v1/policy_enforcement.py",
    "backend/alembic/versions/f13a4b5c6d7e_create_policy_audit_events.py",
    "policy-service/pom.xml",
    "frontend/app/policy/page.tsx",
    "frontend/components/PolicyControlCenter.tsx"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 13 file: $path"
    }
}
Pass "Phase 13 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}
Pass "Python compilation"

python -m pytest tests -q
if ($LASTEXITCODE -ne 0) {
    throw "Full Python test suite failed."
}
Pass "Full Python test suite"

Push-Location backend
try {
    $heads = alembic heads
    if ($LASTEXITCODE -ne 0) {
        throw "alembic heads failed."
    }

    if ($heads -notmatch "f13a4b5c6d7e") {
        throw "Expected Alembic head f13a4b5c6d7e. Got: $heads"
    }
}
finally {
    Pop-Location
}
Pass "Alembic head"

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    config | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose config failed."
}
Pass "Phase 13 Docker Compose config"

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    exec -T backend alembic current | Select-String "f13a4b5c6d7e" | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Docker database is not at Phase 13 Alembic head."
}
Pass "Docker database migration"

$policyHealth = Invoke-RestMethod `
    -Uri "http://localhost:8090/actuator/health"

if ($policyHealth.status -ne "UP") {
    throw "Policy Service health is not UP."
}
Pass "Spring Boot Policy Service health"

$readOnlyBody = @{
    action = "list_containers"
    resource = "tool"
    arguments = @{}
    agentId = "docker-agent"
} | ConvertTo-Json

$readOnly = Invoke-RestMethod `
    -Uri "http://localhost:8090/api/v1/policies/evaluate" `
    -Method POST `
    -ContentType "application/json" `
    -Body $readOnlyBody

if ($readOnly.decision -ne "ALLOW" -or $readOnly.risk -ne "LOW") {
    throw "Read-only policy scenario failed."
}
Pass "ALLOW / LOW policy scenario"

$reviewBody = @{
    action = "send_email"
    resource = "tool"
    arguments = @{}
    agentId = "tool-agent"
} | ConvertTo-Json

$review = Invoke-RestMethod `
    -Uri "http://localhost:8090/api/v1/policies/evaluate" `
    -Method POST `
    -ContentType "application/json" `
    -Body $reviewBody

if ($review.decision -ne "REVIEW" -or $review.risk -ne "HIGH") {
    throw "External side-effect policy scenario failed."
}
Pass "REVIEW / HIGH policy scenario"

$denyBody = @{
    action = "drop_database"
    resource = "tool"
    arguments = @{}
    agentId = "postgres-agent"
} | ConvertTo-Json

$deny = Invoke-RestMethod `
    -Uri "http://localhost:8090/api/v1/policies/evaluate" `
    -Method POST `
    -ContentType "application/json" `
    -Body $denyBody

if ($deny.decision -ne "DENY" -or $deny.risk -ne "CRITICAL") {
    throw "Destructive policy scenario failed."
}
Pass "DENY / CRITICAL policy scenario"

$metrics = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/metrics" `
    -UseBasicParsing

if ($metrics.StatusCode -ne 200) {
    throw "Backend metrics endpoint failed."
}

if ($metrics.Content -notmatch "redpa_policy_evaluations_total") {
    throw "Policy Prometheus metrics were not found."
}
Pass "Policy Prometheus telemetry"

$frontend = Invoke-WebRequest `
    -Uri "http://localhost:3001/policy" `
    -UseBasicParsing

if ($frontend.StatusCode -ne 200) {
    throw "Policy Control Center failed."
}
Pass "Policy Control Center HTTP 200"

docker compose build frontend
if ($LASTEXITCODE -ne 0) {
    throw "Frontend production build failed."
}
Pass "Frontend production build"

Write-Host ""
Write-Host "PHASE 13 COMPLETE" -ForegroundColor Green
Write-Host "Spring Boot Policy Engine + Guardrails + Human Review + Tool/MCP Enforcement + Audit + Observability + BDD + Control Center are verified." -ForegroundColor Green
Write-Host ""
Write-Host "Next: Phase 14." -ForegroundColor Cyan

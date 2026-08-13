$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v2.0.0 - Final Release Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app",
    "frontend/app",
    "frontend/components",
    "docker-compose.yml",
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "docs/archive/v2/RELEASE_NOTES_v2.0.0.md",
    "docs/V2_RELEASE_CHECKLIST.md",
    "docs/V2_PRODUCTION_HARDENING.md"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing required path: $path"
    }
}

Pass "Required v2 files"

# ------------------------------------------------------------
# Python compilation
# ------------------------------------------------------------

python -m compileall -q backend/app

if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}

Pass "Python compilation"

# ------------------------------------------------------------
# Pytest
# ------------------------------------------------------------

if (-not (Test-Path ".\tests")) {
    throw "Test directory '.\tests' was not found."
}

python -m pytest .\tests -q
$pytestExitCode = $LASTEXITCODE

if ($pytestExitCode -ne 0) {
    throw "pytest failed with exit code $pytestExitCode."
}

Pass "pytest"

# ------------------------------------------------------------
# Docker Compose validation
# ------------------------------------------------------------

docker compose config | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "docker compose config failed."
}

Pass "Docker Compose config"

# ------------------------------------------------------------
# Platform health
# ------------------------------------------------------------

$live = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/platform/live"

Pass "Liveness"

$ready = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/platform/ready"

Pass "Readiness"

$health = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/platform/health"

if ($health.status -ne "healthy") {
    throw "Deep health is $($health.status)."
}

Pass "Deep platform health"

# ------------------------------------------------------------
# Performance
# ------------------------------------------------------------

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/performance/snapshot" `
    | Out-Null

Pass "Performance snapshot"

# ------------------------------------------------------------
# Prometheus metrics
# ------------------------------------------------------------

$metrics = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/metrics" `
    -UseBasicParsing

if ($metrics.StatusCode -ne 200) {
    throw "Metrics endpoint failed."
}

Pass "Prometheus metrics"

# ------------------------------------------------------------
# Frontend
# ------------------------------------------------------------

$frontend = Invoke-WebRequest `
    -Uri "http://localhost:3001" `
    -UseBasicParsing

if ($frontend.StatusCode -ne 200) {
    throw "Frontend failed."
}

Pass "Control Center HTTP 200"

# ------------------------------------------------------------
# Protected MCP verification
# ------------------------------------------------------------

Write-Host ""
Write-Host "Protected MCP verification" -ForegroundColor Cyan

$email = Read-Host "RedPA login email"
$securePassword = Read-Host "RedPA login password" -AsSecureString

$credential = New-Object `
    System.Management.Automation.PSCredential(
        $email,
        $securePassword
    )

$password = $credential.GetNetworkCredential().Password

$login = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST `
    -ContentType "application/x-www-form-urlencoded" `
    -Body @{
        username = $email
        password = $password
    }

if (-not $login.access_token) {
    throw "Login returned no access token."
}

$headers = @{
    Authorization = "Bearer $($login.access_token)"
}

Pass "JWT authentication"

# ------------------------------------------------------------
# Verify unauthenticated MCP access is blocked
# ------------------------------------------------------------

$blocked = $false

try {
    Invoke-RestMethod `
        -Uri "http://localhost:8000/api/v1/mcp/servers" `
        | Out-Null
}
catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 401) {
        $blocked = $true
    }
}

if (-not $blocked) {
    throw "MCP registry did not reject unauthenticated access."
}

Pass "MCP authentication boundary"

# ------------------------------------------------------------
# Authenticated MCP control plane
# ------------------------------------------------------------

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/mcp/servers" `
    -Headers $headers `
    | Out-Null

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/mcp/health" `
    -Headers $headers `
    | Out-Null

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/mcp/tools" `
    -Headers $headers `
    | Out-Null

Pass "Authenticated MCP control plane"

# ------------------------------------------------------------
# Frontend production build
# ------------------------------------------------------------

docker compose build frontend

if ($LASTEXITCODE -ne 0) {
    throw "Frontend image build failed."
}

Pass "Frontend production build"

# ------------------------------------------------------------
# Final result
# ------------------------------------------------------------

Write-Host ""
Write-Host "All automated v2 checks passed." -ForegroundColor Green
Write-Host "Review docs/V2_RELEASE_CHECKLIST.md before tagging v2.0.0." -ForegroundColor Cyan
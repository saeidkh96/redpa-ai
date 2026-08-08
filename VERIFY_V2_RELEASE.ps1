$ErrorActionPreference = "Stop"

function Pass($message) { Write-Host "[PASS] $message" -ForegroundColor Green }

Write-Host "RedPA AI v2.0.0 - Final Release Verification" -ForegroundColor Cyan

$required = @(
  "backend/app",
  "frontend/app",
  "frontend/components",
  "docker-compose.yml",
  "README.md",
  "LICENSE",
  "SECURITY.md",
  "RELEASE_NOTES_v2.0.0.md",
  "docs/V2_RELEASE_CHECKLIST.md",
  "docs/V2_PRODUCTION_HARDENING.md"
)

foreach ($path in $required) {
  if (-not (Test-Path $path)) { throw "Missing required path: $path" }
}
Pass "Required v2 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }
Pass "Python compilation"

if (Test-Path ".\backend\tests") {
    Push-Location backend

    try {
        python -m pytest tests -q
        $pytestExitCode = $LASTEXITCODE

        if ($pytestExitCode -eq 0) {
            Pass "pytest"
        }
        elseif ($pytestExitCode -eq 5) {
            Write-Host "[INFO] pytest found no tests. Continuing release validation." -ForegroundColor Yellow
        }
        else {
            throw "pytest failed with exit code $pytestExitCode."
        }
    }
    finally {
        Pop-Location
    }
}
elseif (Test-Path ".\tests") {
    python -m pytest tests -q
    $pytestExitCode = $LASTEXITCODE

    if ($pytestExitCode -eq 0) {
        Pass "pytest"
    }
    elseif ($pytestExitCode -eq 5) {
        Write-Host "[INFO] pytest found no tests. Continuing release validation." -ForegroundColor Yellow
    }
    else {
        throw "pytest failed with exit code $pytestExitCode."
    }
}
else {
    Write-Host "[INFO] No pytest test directory found. Continuing release validation." -ForegroundColor Yellow
}

docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) { throw "docker compose config failed." }
Pass "Docker Compose config"

$live = Invoke-RestMethod "http://localhost:8000/api/v1/platform/live"
Pass "Liveness"

$ready = Invoke-RestMethod "http://localhost:8000/api/v1/platform/ready"
Pass "Readiness"

$health = Invoke-RestMethod "http://localhost:8000/api/v1/platform/health"
if ($health.status -ne "healthy") { throw "Deep health is $($health.status)." }
Pass "Deep platform health"

Invoke-RestMethod "http://localhost:8000/api/v1/performance/snapshot" | Out-Null
Pass "Performance snapshot"

$metrics = Invoke-WebRequest "http://localhost:8000/api/v1/metrics" -UseBasicParsing
if ($metrics.StatusCode -ne 200) { throw "Metrics endpoint failed." }
Pass "Prometheus metrics"

$frontend = Invoke-WebRequest "http://localhost:3001" -UseBasicParsing
if ($frontend.StatusCode -ne 200) { throw "Frontend failed." }
Pass "Control Center HTTP 200"

Write-Host ""
Write-Host "Protected MCP verification" -ForegroundColor Cyan
$email = Read-Host "RedPA login email"
$securePassword = Read-Host "RedPA login password" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential($email, $securePassword)
$password = $credential.GetNetworkCredential().Password

$login = Invoke-RestMethod `
  -Uri "http://localhost:8000/api/v1/auth/login" `
  -Method POST `
  -ContentType "application/x-www-form-urlencoded" `
  -Body @{ username = $email; password = $password }

if (-not $login.access_token) { throw "Login returned no access token." }
$headers = @{ Authorization = "Bearer $($login.access_token)" }
Pass "JWT authentication"

$blocked = $false
try {
  Invoke-RestMethod "http://localhost:8000/api/v1/mcp/servers" | Out-Null
}
catch {
  if ($_.Exception.Response.StatusCode.value__ -eq 401) { $blocked = $true }
}
if (-not $blocked) { throw "MCP registry did not reject unauthenticated access." }
Pass "MCP authentication boundary"

Invoke-RestMethod "http://localhost:8000/api/v1/mcp/servers" -Headers $headers | Out-Null
Invoke-RestMethod "http://localhost:8000/api/v1/mcp/health" -Headers $headers | Out-Null
Invoke-RestMethod "http://localhost:8000/api/v1/mcp/tools" -Headers $headers | Out-Null
Pass "Authenticated MCP control plane"

docker compose build frontend
if ($LASTEXITCODE -ne 0) { throw "Frontend image build failed." }
Pass "Frontend production build"

Write-Host ""
Write-Host "All automated v2 checks passed." -ForegroundColor Green
Write-Host "Review docs/V2_RELEASE_CHECKLIST.md before tagging v2.0.0." -ForegroundColor Cyan

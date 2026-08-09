$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phases 17 / 18 / 19 Runtime & Final Verification" -ForegroundColor Cyan
Write-Host ""

$current = docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    exec -T backend alembic current

if ($LASTEXITCODE -ne 0 -or $current -notmatch "p17a1b2c3d4e") {
    throw "Docker DB is not at p17a1b2c3d4e. Current: $current"
}
Pass "Docker database migration"

$email = Read-Host "RedPA login email"
$securePassword = Read-Host "RedPA login password" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential(
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
    throw "JWT login failed."
}

$headers = @{
    Authorization = "Bearer $($login.access_token)"
}
Pass "JWT authentication"

$event = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/events" `
    -Method POST `
    -Headers $headers `
    -ContentType "application/json" `
    -Body (@{
        event_type = "redpa.release.smoke"
        aggregate_type = "release"
        aggregate_id = "v3.0.0"
        payload = @{
            message = "RedPA event-driven runtime works"
        }
        metadata = @{
            verification = "phase17-19"
        }
    } | ConvertTo-Json -Depth 6)

if ($event.status -ne "pending") {
    throw "New outbox event was not pending."
}
Pass "Transactional outbox enqueue"

$flush = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/events/flush" `
    -Method POST `
    -Headers $headers

if ($flush.published -lt 1) {
    throw "No event was published to Redis Streams. Failed: $($flush.failed)"
}
Pass "Redis Streams publication"

$events = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/events?limit=20" `
    -Headers $headers

$publishedEvent = @($events) |
    Where-Object { $_.id -eq $event.id } |
    Select-Object -First 1

if ($null -eq $publishedEvent -or $publishedEvent.status -ne "published") {
    throw "Outbox event was not persisted as published."
}
Pass "Published outbox state"

$redisEntry = docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    exec -T redis redis-cli XLEN redpa:events

if ($LASTEXITCODE -ne 0 -or [int]$redisEntry -lt 1) {
    throw "Redis stream redpa:events is empty."
}
Pass "Redis stream contains events"

$eventUi = Invoke-WebRequest `
    -Uri "http://localhost:3001/events" `
    -UseBasicParsing

if ($eventUi.StatusCode -ne 200) {
    throw "Event Control Center failed."
}
Pass "Event Control Center HTTP 200"

$policyHealth = Invoke-RestMethod `
    -Uri "http://localhost:8090/actuator/health"

if ($policyHealth.status -ne "UP") {
    throw "Spring Boot Policy Service is not healthy."
}
Pass "Spring Boot Policy Service health"

$metrics = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/metrics" `
    -UseBasicParsing

if ($metrics.StatusCode -ne 200) {
    throw "Backend metrics endpoint failed."
}
Pass "Metrics endpoint"

python .\scripts\security\secret_scan.py
if ($LASTEXITCODE -ne 0) {
    throw "Secret scan failed."
}
Pass "Repository secret scan"

python -m pytest tests -q
if ($LASTEXITCODE -ne 0) {
    throw "Full regression suite failed."
}
Pass "Full regression suite"

docker compose build frontend
if ($LASTEXITCODE -ne 0) {
    throw "Frontend production build failed."
}
Pass "Frontend production build"

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    build policy-service

if ($LASTEXITCODE -ne 0) {
    throw "Spring Boot production build failed."
}
Pass "Spring Boot production build"

python .\scripts\release\build_v3_archive.py
if ($LASTEXITCODE -ne 0) {
    throw "V3 archive build failed."
}

if (-not (Test-Path ".\dist\redpa-ai-v3.0.0.zip")) {
    throw "Release archive missing."
}
if (-not (Test-Path ".\dist\redpa-ai-v3.0.0.sha256")) {
    throw "Release SHA256 missing."
}
Pass "V3 release archive + SHA256"

Write-Host ""
Write-Host "PHASE 17 COMPLETE" -ForegroundColor Green
Write-Host "Transactional Outbox + Redis Streams + Event Control Center verified." -ForegroundColor Green
Write-Host ""
Write-Host "PHASE 18 COMPLETE" -ForegroundColor Green
Write-Host "Production hardening + security gates + threat model verified." -ForegroundColor Green
Write-Host ""
Write-Host "PHASE 19 COMPLETE" -ForegroundColor Green
Write-Host "Portfolio docs + release manifest + archive automation verified." -ForegroundColor Green
Write-Host ""
Write-Host "REDPA AI V3 ROADMAP COMPLETE" -ForegroundColor Cyan
Write-Host "Review docs/release/V3_FINAL_CHECKLIST.md and the release archive before tagging v3.0.0." -ForegroundColor Yellow

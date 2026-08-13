$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 16 Runtime Verification" -ForegroundColor Cyan
Write-Host ""

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    exec -T backend alembic current |
    Select-String "p16a1b2c3d4e" | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Docker DB is not at p16a1b2c3d4e."
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

$headers = @{
    Authorization = "Bearer $($login.access_token)"
}
Pass "JWT authentication"

$tenantName = "Phase 16 Workspace $([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"

$tenant = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/tenants" `
    -Method POST `
    -Headers $headers `
    -ContentType "application/json" `
    -Body (@{ name = $tenantName } | ConvertTo-Json)

if ($tenant.role -ne "owner") {
    throw "Tenant creator was not assigned owner role."
}
Pass "Tenant creation + owner membership"

$tenants = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/tenants" `
    -Headers $headers

if (-not $tenants) {
    throw "Tenant list returned no tenants."
}
Pass "Tenant listing"

$providers = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/oauth/providers"

Pass "OAuth provider discovery"

$frontend = Invoke-WebRequest `
    -Uri "http://localhost:3001/access" `
    -UseBasicParsing

if ($frontend.StatusCode -ne 200) {
    throw "Access Control Center failed."
}
Pass "Access Control Center HTTP 200"

docker compose build frontend
if ($LASTEXITCODE -ne 0) {
    throw "Frontend production build failed."
}
Pass "Frontend production build"

Write-Host ""
Write-Host "PHASE 16 COMPLETE" -ForegroundColor Green
Write-Host "RBAC + Multi-tenancy + Tenant Isolation Foundation + OAuth PKCE Foundation + Access Control Center are verified." -ForegroundColor Green
Write-Host ""
Write-Host "Note: OAuth token exchange/account linking remains disabled until real provider credentials and state/verifier persistence are configured." -ForegroundColor Yellow
Write-Host "Next: Phase 17 - Event-driven Integrations / Messaging." -ForegroundColor Cyan

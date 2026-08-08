$ErrorActionPreference = "Stop"

Write-Host "RedPA AI v2 - Phases 10.6 / 10.7 authenticated verification" -ForegroundColor Cyan
Write-Host ""

$email = Read-Host "RedPA login email"
$securePassword = Read-Host "RedPA login password" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential($email, $securePassword)
$password = $credential.GetNetworkCredential().Password

$form = @{
    username = $email
    password = $password
}

$login = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST `
    -ContentType "application/x-www-form-urlencoded" `
    -Body $form

if (-not $login.access_token) {
    throw "Login succeeded without an access token."
}

$headers = @{
    Authorization = "Bearer $($login.access_token)"
}

Write-Host "[PASS] Authentication" -ForegroundColor Green

$servers = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/mcp/servers" `
    -Headers $headers
Write-Host "[PASS] 10.6 MCP server registry" -ForegroundColor Green

$health = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/mcp/health" `
    -Headers $headers
Write-Host "[PASS] 10.6 MCP health" -ForegroundColor Green

$tools = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/mcp/tools" `
    -Headers $headers
Write-Host "[PASS] 10.6 MCP tool catalog" -ForegroundColor Green

$platform = Invoke-RestMethod "http://localhost:8000/api/v1/platform/health"
Write-Host "[PASS] 10.7 Platform health -> $($platform.status)" -ForegroundColor Green

$performance = Invoke-RestMethod "http://localhost:8000/api/v1/performance/snapshot"
Write-Host "[PASS] 10.7 Performance snapshot" -ForegroundColor Green

$metrics = Invoke-WebRequest "http://localhost:8000/api/v1/metrics" -UseBasicParsing
if ($metrics.StatusCode -ne 200) {
    throw "Metrics endpoint did not return HTTP 200."
}
Write-Host "[PASS] 10.7 Prometheus metrics -> HTTP 200" -ForegroundColor Green

$frontend = Invoke-WebRequest "http://localhost:3001" -UseBasicParsing
if ($frontend.StatusCode -ne 200) {
    throw "Frontend did not return HTTP 200."
}
Write-Host "[PASS] Control Center -> HTTP 200" -ForegroundColor Green

Write-Host ""
Write-Host "Open http://localhost:3001" -ForegroundColor Cyan

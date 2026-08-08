$ErrorActionPreference = "Stop"

Write-Host "RedPA AI v2 - Phase 10.2 Agent Control Center" -ForegroundColor Cyan

$required = @(
    "frontend/components/Dashboard.tsx",
    "frontend/app/globals.css"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing required file: $path"
    }
}

Write-Host "[PASS] Phase 10.2 files installed" -ForegroundColor Green

Write-Host ""
Write-Host "Checking backend Agent APIs..." -ForegroundColor Cyan

$agents = Invoke-RestMethod http://localhost:8000/api/v1/agents
Write-Host "[PASS] /api/v1/agents -> $($agents.total) registered agents" -ForegroundColor Green

$health = Invoke-RestMethod http://localhost:8000/api/v1/agents/health
Write-Host "[PASS] /api/v1/agents/health -> $($health.status)" -ForegroundColor Green

$remotes = Invoke-RestMethod http://localhost:8000/api/v1/agents/remotes
Write-Host "[PASS] /api/v1/agents/remotes -> $($remotes.total) remote agents" -ForegroundColor Green

Write-Host ""
Write-Host "Rebuild the frontend:" -ForegroundColor Cyan
Write-Host "docker compose up -d --build --force-recreate frontend"
Write-Host ""
Write-Host "Then open:"
Write-Host "http://localhost:3001"

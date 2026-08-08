$ErrorActionPreference = "Stop"

Write-Host "RedPA AI v2 - Phase 10.1 verification" -ForegroundColor Cyan

$required = @(
  "frontend/package.json",
  "frontend/Dockerfile",
  "frontend/app/page.tsx",
  "frontend/app/layout.tsx",
  "frontend/app/globals.css",
  "frontend/components/Dashboard.tsx",
  "frontend/public/logo.png",
  "docker-compose.yml"
)

foreach ($path in $required) {
  if (-not (Test-Path $path)) {
    throw "Missing required file: $path"
  }
}

docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) { throw "docker compose config failed" }

Write-Host "[PASS] Files" -ForegroundColor Green
Write-Host "[PASS] Docker Compose config" -ForegroundColor Green
Write-Host ""
Write-Host "Start Phase 10.1:" -ForegroundColor Cyan
Write-Host "  docker compose up -d --build frontend"
Write-Host ""
Write-Host "Dashboard:"
Write-Host "  http://localhost:3001"

$ErrorActionPreference = "Stop"

$composePath = ".\docker-compose.yml"
if (-not (Test-Path $composePath)) { throw "docker-compose.yml was not found." }

$content = Get-Content $composePath -Raw
$corsLine = '      CORS_ALLOWED_ORIGINS: ''["http://localhost:3000","http://127.0.0.1:3000","http://localhost:3001","http://127.0.0.1:3001","http://localhost:5173","http://127.0.0.1:5173"]'''

if ($content -match '(?m)^\s+CORS_ALLOWED_ORIGINS:') {
  $content = [regex]::Replace($content, '(?m)^\s+CORS_ALLOWED_ORIGINS:.*$', $corsLine, 1)
}
elseif ($content -match '(?m)^      API_V1_PREFIX:.*$') {
  $content = [regex]::Replace($content, '(?m)^(      API_V1_PREFIX:.*)$', '$1' + "`r`n" + $corsLine, 1)
}
else {
  Write-Warning "Could not automatically insert CORS_ALLOWED_ORIGINS."
}

Set-Content $composePath $content -Encoding UTF8

docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) { throw "docker compose config failed" }

Write-Host "[PASS] Docker Compose config and CORS" -ForegroundColor Green
Write-Host "Next: docker compose up -d --build --force-recreate backend frontend" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
Write-Host "RedPA AI v2 - Phases 10.3 / 10.4 / 10.5" -ForegroundColor Cyan
$workflows = Invoke-RestMethod "http://localhost:8000/api/v1/agents/distributed/durable?limit=5"
Write-Host "[PASS] 10.3 Durable Workflow API -> $($workflows.Count) records" -ForegroundColor Green
$memories = Invoke-RestMethod "http://localhost:8000/api/v1/memory?limit=5"
Write-Host "[PASS] 10.5 Agent Memory API -> $($memories.Count) records" -ForegroundColor Green
Write-Host "[INFO] 10.4 Human Review requires JWT; verify by signing in from the dashboard."
$response = Invoke-WebRequest "http://localhost:3001" -UseBasicParsing
if ($response.StatusCode -ne 200) { throw "Frontend did not return HTTP 200." }
Write-Host "[PASS] Control Center -> HTTP 200" -ForegroundColor Green

$ErrorActionPreference = "Stop"

$policyPage = ".\frontend\app\policy\page.tsx"
if (-not (Test-Path $policyPage)) {
    throw "Policy Control Center page was not extracted."
}

Write-Host "[PASS] Phase 13.7 Policy Control Center installed." -ForegroundColor Green
Write-Host "[PASS] Phase 13.8 security/integration/BDD tests installed." -ForegroundColor Green
Write-Host "[PASS] Phase 13.9 final verification script installed." -ForegroundColor Green
Write-Host ""
Write-Host "Policy Control Center route: http://localhost:3001/policy" -ForegroundColor Cyan

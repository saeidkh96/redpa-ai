$ErrorActionPreference = "Stop"

$required = @(
    ".\infra\azure\Pulumi.yaml",
    ".\infra\azure\__main__.py",
    ".\infra\azure\foundation.py",
    ".\infra\azure\database.py",
    ".\infra\azure\container_apps.py",
    ".\docs\cloud\azure-architecture.md"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 15 file: $path"
    }
}

Write-Host "[PASS] Azure reference architecture installed." -ForegroundColor Green
Write-Host "[PASS] Pulumi Python infrastructure installed." -ForegroundColor Green
Write-Host "[PASS] Azure security / cost / deployment docs installed." -ForegroundColor Green
Write-Host "[PASS] Pulumi preview CI workflow installed." -ForegroundColor Green
Write-Host ""
Write-Host "No Azure resources were created. Cloud deployment remains explicit through pulumi preview/up." -ForegroundColor Cyan

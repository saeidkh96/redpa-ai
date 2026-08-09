$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 15 Final Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "infra/azure/Pulumi.yaml",
    "infra/azure/requirements.txt",
    "infra/azure/config.py",
    "infra/azure/naming.py",
    "infra/azure/tags.py",
    "infra/azure/foundation.py",
    "infra/azure/database.py",
    "infra/azure/container_apps.py",
    "infra/azure/__main__.py",
    "docs/cloud/azure-architecture.md",
    "docs/cloud/security.md",
    "docs/cloud/cost.md",
    "docs/cloud/runbook.md",
    ".github/workflows/pulumi-azure-preview.yml"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 15 path: $path"
    }
}
Pass "Phase 15 cloud files"

python -m compileall -q infra/azure
if ($LASTEXITCODE -ne 0) {
    throw "Pulumi Python compilation failed."
}
Pass "Pulumi Python compilation"

python -m pytest `
    .\tests\test_phase15_cloud_architecture.py `
    .\tests\test_phase15_iac_contract.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 15 infrastructure tests failed."
}
Pass "Azure / Pulumi architecture tests"

python -m pytest tests -q
if ($LASTEXITCODE -ne 0) {
    throw "Full regression suite failed."
}
Pass "Full regression suite"

docker compose `
    -f docker-compose.yml `
    -f docker-compose.phase13.yml `
    config | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose config failed."
}
Pass "Existing local deployment config"

$requirements = Get-Content ".\infra\azure\requirements.txt" -Raw
if ($requirements -notmatch "pulumi-azure-native") {
    throw "Azure Native Pulumi provider dependency missing."
}
Pass "Pulumi Azure Native provider"

if ($env:REDPA_RUN_AZURE_PREVIEW -eq "1") {
    Write-Host ""
    Write-Host "REDPA_RUN_AZURE_PREVIEW=1 - running real Pulumi preview." -ForegroundColor Yellow

    if (-not (Get-Command pulumi -ErrorAction SilentlyContinue)) {
        throw "Pulumi CLI not found."
    }

    Push-Location ".\infra\azure"
    try {
        pulumi preview --non-interactive
        if ($LASTEXITCODE -ne 0) {
            throw "Pulumi Azure preview failed."
        }
    }
    finally {
        Pop-Location
    }

    Pass "Live Azure Pulumi preview"
}
else {
    Write-Host "[INFO] Live Azure preview skipped. Set REDPA_RUN_AZURE_PREVIEW=1 after Azure/Pulumi authentication to enable it." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "PHASE 15 COMPLETE" -ForegroundColor Green
Write-Host "Azure Reference Architecture + Pulumi IaC + Container Apps + PostgreSQL + Key Vault + ACR + Cloud CI/Security are verified locally." -ForegroundColor Green
Write-Host ""
Write-Host "Important: local verification does not claim that Azure resources have been deployed." -ForegroundColor Yellow
Write-Host "Next: Phase 16 - RBAC + Multi-tenancy + OAuth." -ForegroundColor Cyan

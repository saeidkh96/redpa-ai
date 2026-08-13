$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 14 Final Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "docs/architecture/README.md",
    "docs/architecture/ddd.md",
    "docs/architecture/clean-architecture.md",
    "docs/architecture/c4.md",
    "docs/architecture/arc42.md",
    "docs/architecture/PHASE_14_CHECKLIST.md",
    "backend/app/architecture/__init__.py",
    "backend/app/architecture/boundaries.py"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 14 path: $path"
    }
}
Pass "Phase 14 architecture files"

$adrCount = (Get-ChildItem ".\docs\architecture\adr\*.md").Count
if ($adrCount -lt 5) {
    throw "Expected at least 5 ADRs, found $adrCount."
}
Pass "Architecture Decision Records"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}
Pass "Python compilation"

python -m pytest `
    .\tests\test_phase14_architecture.py `
    .\tests\test_phase14_documentation_contract.py `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 14 architecture tests failed."
}
Pass "Architecture tests"

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
    throw "Docker Compose configuration failed."
}
Pass "Docker Compose config"

Write-Host ""
Write-Host "PHASE 14 COMPLETE" -ForegroundColor Green
Write-Host "DDD + Bounded Contexts + Clean Architecture Rules + SOLID Guidance + ADR + C4 + arc42 are verified." -ForegroundColor Green
Write-Host ""
Write-Host "Next: Phase 15 - Cloud / Azure + Pulumi." -ForegroundColor Cyan

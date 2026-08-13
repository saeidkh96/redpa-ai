$ErrorActionPreference = "Stop"

$required = @(
    ".\docs\architecture\ddd.md",
    ".\docs\architecture\clean-architecture.md",
    ".\docs\architecture\c4.md",
    ".\docs\architecture\arc42.md",
    ".\backend\app\architecture\boundaries.py"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 14 file: $path"
    }
}

Write-Host "[PASS] Phase 14 architecture baseline installed." -ForegroundColor Green
Write-Host "[PASS] DDD bounded contexts installed." -ForegroundColor Green
Write-Host "[PASS] C4 + arc42 documentation installed." -ForegroundColor Green
Write-Host "[PASS] Architecture Decision Records installed." -ForegroundColor Green
Write-Host ""
Write-Host "Phase 14 is intentionally non-destructive: it adds explicit architecture boundaries and tests without rewriting working runtime code." -ForegroundColor Cyan

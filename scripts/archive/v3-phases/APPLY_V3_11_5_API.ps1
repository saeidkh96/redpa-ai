$ErrorActionPreference = "Stop"

$routerPath = ".\backend\app\api\v1\router.py"

if (-not (Test-Path $routerPath)) {
    throw "Router file not found: $routerPath"
}

$content = Get-Content $routerPath -Raw

if ($content -notmatch "evaluations") {
    $importCandidates = @(
        "from app.api.v1 import",
        "from app.api.v1."
    )

    if ($content -match "from app\.api\.v1 import \(") {
        $content = $content -replace "from app\.api\.v1 import \(", "from app.api.v1 import (`r`n    evaluations,"
    }
    elseif ($content -match "from app\.api\.v1 import ") {
        $content = "from app.api.v1 import evaluations`r`n" + $content
    }
    else {
        $content = "from app.api.v1 import evaluations`r`n" + $content
    }
}

if ($content -notmatch "evaluations\.router") {
    $patterns = @(
        "api_router\.include_router",
        "router\.include_router"
    )

    $target = $null
    foreach ($pattern in $patterns) {
        $matches = [regex]::Matches($content, $pattern)
        if ($matches.Count -gt 0) {
            $target = $pattern
            break
        }
    }

    if ($null -eq $target) {
        throw "Could not find include_router pattern in router.py. Add evaluations.router manually."
    }

    if ($target -eq "api_router\.include_router") {
        $content += "`r`napi_router.include_router(evaluations.router)`r`n"
    }
    else {
        $content += "`r`nrouter.include_router(evaluations.router)`r`n"
    }
}

Set-Content $routerPath $content -Encoding UTF8
Write-Host "[PASS] Evaluation API router registered." -ForegroundColor Green

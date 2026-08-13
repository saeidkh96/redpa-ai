$ErrorActionPreference = "Stop"

$routerPath = ".\backend\app\api\v1\router.py"

if (-not (Test-Path $routerPath)) {
    throw "Router file not found: $routerPath"
}

$content = Get-Content $routerPath -Raw

if ($content -notmatch "model_gateway") {
    if ($content -match "from app\.api\.v1 import \(") {
        $content = $content -replace `
            "from app\.api\.v1 import \(", `
            "from app.api.v1 import (`r`n    model_gateway,"
    }
    else {
        $content = "from app.api.v1 import model_gateway`r`n" + $content
    }
}

if ($content -notmatch "model_gateway\.router") {
    if ($content -match "api_router\.include_router") {
        $content += "`r`napi_router.include_router(model_gateway.router)`r`n"
    }
    elseif ($content -match "router\.include_router") {
        $content += "`r`nrouter.include_router(model_gateway.router)`r`n"
    }
    else {
        throw "Could not find include_router pattern in router.py."
    }
}

Set-Content $routerPath $content -Encoding UTF8
Write-Host "[PASS] Model Gateway API router registered." -ForegroundColor Green

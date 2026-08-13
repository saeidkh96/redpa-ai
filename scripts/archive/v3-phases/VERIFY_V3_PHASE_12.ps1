$ErrorActionPreference = "Stop"

function Pass($message) {
    Write-Host "[PASS] $message" -ForegroundColor Green
}

Write-Host "RedPA AI v3 - Phase 12 Final Verification" -ForegroundColor Cyan
Write-Host ""

$required = @(
    "backend/app/model_gateway/contracts.py",
    "backend/app/model_gateway/config.py",
    "backend/app/model_gateway/factory.py",
    "backend/app/model_gateway/registry.py",
    "backend/app/model_gateway/routing.py",
    "backend/app/model_gateway/reliability.py",
    "backend/app/model_gateway/gateway.py",
    "backend/app/model_gateway/bootstrap.py",
    "backend/app/model_gateway/providers/ollama.py",
    "backend/app/model_gateway/providers/openai_compatible.py",
    "backend/app/model_gateway/providers/mock.py",
    "backend/app/api/v1/model_gateway.py",
    "backend/app/schemas/model_gateway.py",
    "frontend/components/ModelGatewayDashboard.tsx",
    "frontend/app/model-gateway/page.tsx"
)

foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing Phase 12 path: $path"
    }
}
Pass "Phase 12 files"

python -m compileall -q backend/app
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed."
}
Pass "Python compilation"

python -m pytest .\tests -q
if ($LASTEXITCODE -ne 0) {
    throw "Full test suite failed."
}
Pass "Full test suite"

$routerContent = Get-Content ".\backend\app\api\v1\router.py" -Raw
if ($routerContent -notmatch "model_gateway\.router") {
    throw "Model Gateway router is not registered."
}
Pass "Model Gateway API registration"

docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "docker compose config failed."
}
Pass "Docker Compose config"

$frontend = Invoke-WebRequest `
    "http://localhost:3001/model-gateway" `
    -UseBasicParsing

if ($frontend.StatusCode -ne 200) {
    throw "Model Gateway Control Center failed."
}
Pass "Model Gateway Control Center HTTP 200"

Write-Host ""
Write-Host "Protected Model Gateway smoke test" -ForegroundColor Cyan

$email = Read-Host "RedPA login email"
$securePassword = Read-Host "RedPA login password" -AsSecureString
$credential = New-Object `
    System.Management.Automation.PSCredential(
        $email,
        $securePassword
    )
$password = $credential.GetNetworkCredential().Password

$login = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST `
    -ContentType "application/x-www-form-urlencoded" `
    -Body @{
        username = $email
        password = $password
    }

if (-not $login.access_token) {
    throw "Login returned no access token."
}

$headers = @{
    Authorization = "Bearer $($login.access_token)"
}
Pass "JWT authentication"

$blocked = $false
try {
    Invoke-RestMethod `
        "http://localhost:8000/api/v1/model-gateway/providers" `
        | Out-Null
}
catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 401) {
        $blocked = $true
    }
}

if (-not $blocked) {
    throw "Model Gateway providers endpoint did not reject unauthenticated access."
}
Pass "Model Gateway authentication boundary"

$providers = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/model-gateway/providers" `
    -Headers $headers

if (-not $providers) {
    throw "No Model Gateway providers were returned."
}
Pass "Provider registry API"

$health = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/model-gateway/health" `
    -Headers $headers

$ollamaHealth = $health |
    Where-Object { $_.provider -eq "ollama" } |
    Select-Object -First 1

if ($null -eq $ollamaHealth) {
    throw "Ollama provider health was not returned."
}

if (-not $ollamaHealth.available) {
    throw "Ollama provider is unavailable."
}
Pass "Ollama provider health"

$routeBody = @{
    agent_id = "research-agent"
    capability = "chat"
} | ConvertTo-Json

$route = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/model-gateway/route" `
    -Method POST `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $routeBody

if (-not $route.provider) {
    throw "Routing preview returned no provider."
}
Pass "Routing strategy"

$invokeBody = @{
    messages = @(
        @{
            role = "user"
            content = "Reply with exactly: RedPA gateway works"
        }
    )
    agent_id = "research-agent"
    capability = "chat"
    temperature = 0
} | ConvertTo-Json -Depth 5

$invoke = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/model-gateway/invoke" `
    -Method POST `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $invokeBody

if (-not $invoke.content) {
    throw "Model Gateway invoke returned empty content."
}

if (-not $invoke.provider) {
    throw "Model Gateway invoke returned no provider."
}
Pass "Live Model Gateway invoke"

$circuits = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/model-gateway/circuits" `
    -Headers $headers

Pass "Circuit breaker API"

docker compose build frontend
if ($LASTEXITCODE -ne 0) {
    throw "Frontend production build failed."
}
Pass "Frontend production build"

Write-Host ""
Write-Host "PHASE 12 COMPLETE" -ForegroundColor Green
Write-Host "Multi-LLM Provider Abstraction + Adapters + Factory + Registry + Routing + Reliability + API + Control Center + TDD are verified." -ForegroundColor Green
Write-Host "Next: Phase 13 - Guardrails & Policy Engine." -ForegroundColor Cyan

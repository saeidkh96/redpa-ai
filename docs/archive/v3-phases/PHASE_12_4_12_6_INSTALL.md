# RedPA AI v3 — Phase 12.4 / 12.5 / 12.6

## 12.4 Routing Strategy

Adds:

- explicit provider/model routing;
- per-agent provider/model routing;
- capability-aware routing;
- default provider selection;
- fallback provider chains;
- Strategy Pattern via composable routing policies.

Optional environment configuration:

```env
MODEL_GATEWAY_DEFAULT_PROVIDER=ollama
MODEL_GATEWAY_FALLBACK_PROVIDERS=openai-compatible

MODEL_GATEWAY_AGENT_ROUTES_JSON={"research-agent":{"provider":"ollama","model":"qwen2.5:7b","fallback_providers":[]}}
```

Do not configure a fallback provider unless it is enabled and intentionally configured.

## 12.5 Reliability

Adds:

- bounded retries;
- async timeout enforcement;
- retryable/non-retryable error distinction;
- per-provider circuit breaker;
- fallback execution;
- provider health aggregation.

The default reliability policy is conservative:

```text
attempts = 2
timeout = 120 seconds
```

Phase 12.7+ can expose these settings in the Control Center.

## 12.6 Model Gateway API

Protected endpoints:

```text
GET  /api/v1/model-gateway/providers
GET  /api/v1/model-gateway/health
GET  /api/v1/model-gateway/circuits
POST /api/v1/model-gateway/route
POST /api/v1/model-gateway/invoke
```

The endpoints require the existing RedPA authenticated-user dependency.

## Install

Extract this ZIP into the repository root and replace files when prompted.

Register the router once:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\APPLY_V3_12_6_API.ps1
```

Verify:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\VERIFY_V3_12_4_12_6.ps1
```

If verification passes:

```powershell
docker compose up -d --build --force-recreate backend
```

Then log in and smoke-test the protected API using the same JWT flow already used for MCP verification.

No database migration is required.

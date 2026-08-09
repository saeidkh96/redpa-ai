# RedPA AI v3 — Phase 13.1 / 13.2 / 13.3

## 13.1 Guardrail Domain + Contracts

Python-side guardrail boundary:

- `GuardrailDecision`: `ALLOW`, `REVIEW`, `DENY`
- `RiskLevel`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- provider-neutral policy request/evaluation contracts
- policy client
- conservative fail-closed behavior
- `GuardedToolService` facade around the existing `ToolService`

The existing `ToolService` is intentionally not replaced globally in these
sub-phases. That avoids breaking MCP/A2A behavior while policy enforcement is
introduced and tested.

## 13.2 Java / Spring Boot Policy Service

A real Spring Boot microservice is added under:

```text
policy-service/
```

Architecture:

```text
api/
application/
domain/
infrastructure/rules/
```

This gives RedPA a real Java/Spring Boot service with clear domain/application
boundaries rather than a demonstration-only Java project.

Runtime endpoint:

```text
POST http://localhost:8090/api/v1/policies/evaluate
GET  http://localhost:8090/actuator/health
```

## 13.3 Policy Rules + BDD + FastAPI Integration

Initial rules:

- read-only tool actions -> `ALLOW / LOW`
- external side effects -> `REVIEW / HIGH`
- destructive operations -> `DENY / CRITICAL`
- unknown actions -> `REVIEW / MEDIUM`

BDD scenarios are implemented with Cucumber.

Protected RedPA endpoints:

```text
POST /api/v1/guardrails/evaluate
GET  /api/v1/guardrails/health
```

## Install

Extract the ZIP into the RedPA repository root.

Register the FastAPI router:

```powershell
powershell -ExecutionPolicy Bypass -File .\APPLY_V3_13_1_13_3.ps1
```

Verify source, Python tests, Compose, Spring Boot tests and Cucumber BDD:

```powershell
powershell -ExecutionPolicy Bypass -File .\VERIFY_V3_13_1_13_3.ps1
```

## Start Phase 13 runtime

Phase 13 deliberately uses a Compose override instead of blindly rewriting the
large existing `docker-compose.yml`.

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.phase13.yml `
  up -d --build policy-service backend
```

Check:

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.phase13.yml `
  ps policy-service backend
```

Policy service direct smoke test:

```powershell
$body = @{
  action = "list_containers"
  resource = "tool"
  arguments = @{}
  agentId = "docker-agent"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:8090/api/v1/policies/evaluate" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

Expected:

```text
decision      ALLOW
risk          LOW
policyVersion 13.3.0
```

Try these actions afterwards:

```text
send_email    -> REVIEW / HIGH
drop_database -> DENY / CRITICAL
unknown_xyz   -> REVIEW / MEDIUM
```

No database migration is required for Phase 13.1-13.3.

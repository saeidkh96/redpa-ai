# RedPA AI v3 — Phase 13.4 / 13.5 / 13.6

## 13.4 — Human Review bridge

`PolicyEnforcementService` converts a `REVIEW` policy decision into a persisted
RedPA `HumanReview` whenever a conversation is supplied.

The review stores:

- policy version;
- matched rules;
- execution boundary;
- requested action;
- resource;
- arguments;
- workflow id.

An already approved execution can pass `approval_granted=true`; `DENY` is never
overridden.

## 13.5 — Guarded internal/MCP execution

`GuardedExecutionService` is the policy-enforced execution boundary for:

- internal RedPA tools;
- qualified MCP tools.

Flow:

```text
Request
  -> Policy Service
      -> ALLOW  -> execute
      -> REVIEW -> Human Review / stop
      -> DENY   -> stop
```

The original `ToolService` and `MCPService` remain low-level executors. This
keeps one explicit policy boundary instead of duplicating policy logic in every
tool implementation.

## 13.6 — Audit + observability

Every enforcement decision is persisted to `policy_audit_events`.

Prometheus metrics:

```text
redpa_policy_evaluations_total
redpa_policy_enforcement_total
redpa_policy_review_created_total
redpa_policy_evaluation_duration_seconds
```

Authenticated API:

```text
POST /api/v1/policy/enforce
GET  /api/v1/policy/audit
```

## Install

Extract into the repository root, then:

```powershell
powershell -ExecutionPolicy Bypass -File .\APPLY_V3_13_4_13_6.ps1
powershell -ExecutionPolicy Bypass -File .\VERIFY_V3_13_4_13_6.ps1
```

Apply the migration:

```powershell
cd backend
alembic upgrade head
alembic current
cd ..
```

Rebuild:

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.phase13.yml `
  up -d --build --force-recreate policy-service backend
```

The next smoke test should use an existing RedPA conversation ID so that a
`REVIEW` decision can prove that a real Human Review record is created.

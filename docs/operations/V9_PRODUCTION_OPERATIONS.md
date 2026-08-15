# RedPA AI V9 — Production Cloud & Autonomous Operations

V9 adds an incident-response and release-readiness layer on top of the V8 analytics, automation, SLO and connector platform.

## Operations flow

```text
Prometheus / operator signal
        -> persisted incident
        -> V9 Ops Agent diagnosis
        -> recommendation
        -> explicit Human-in-the-Loop approval
        -> allowlisted stateless restart
        -> post-action verification
        -> resolved incident
```

The local Ops Agent exposes only a narrow Docker remediation surface. Container names must start with `redpa-`, and automatic restart is blocked for PostgreSQL, Qdrant and Redis. All restart side effects require explicit approval.

## API

- `POST /api/v1/operations/v9/incidents`
- `GET /api/v1/operations/v9/incidents`
- `POST /api/v1/operations/v9/incidents/{id}/diagnose`
- `POST /api/v1/operations/v9/incidents/{id}/remediate`
- `POST /api/v1/operations/v9/cost/estimate`
- `POST /api/v1/operations/v9/release/readiness`

## Release readiness

Promotion requires all of the following:

- availability target passed;
- p95 latency target passed;
- zero open critical incidents;
- security gate passed;
- regression gate passed.

## Backup and disaster recovery

`scripts/operations/postgres_backup.py` creates a custom-format PostgreSQL backup from the local Docker database. `postgres_restore.py` requires `--confirm` because restore is destructive.

## Cloud boundary

Azure/Pulumi infrastructure remains production-oriented infrastructure-as-code until executed against a real Azure subscription. V9 does not claim a live Azure deployment merely because the stack previews or validates locally.

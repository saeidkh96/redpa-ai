# RedPA AI V8.0 — Enterprise AI Operations & Automation

V8 combines three portfolio/production concerns into one milestone: analytics/KPIs, enterprise connectors/automation, and cloud reliability evidence.

## Analytics & KPI Platform

The analytics layer stores generic metric facts in `analytics_fact_events` with numeric `value`, optional `weight`, JSON dimensions, metadata and event time.

Supported aggregations:

- `sum`
- `avg`
- `weighted_avg`
- `count`
- `min`
- `max`

Dimensions are queried from JSONB, allowing slices such as business unit, agency, role, cost centre, workspace, agent or time-generated categories without schema changes for every new dimension.

API:

```text
POST /api/v1/analytics/events
GET  /api/v1/analytics/catalog
POST /api/v1/analytics/query
```

Control Plane:

```text
http://localhost:3001/control-plane/analytics
```

## Enterprise Connectors & Automation

V8 adds a persisted connector registry and delivery audit trail.

Connector kinds:

- generic webhook
- Slack incoming webhook
- GitHub repository-dispatch style endpoint
- n8n webhook

External side effects are approval-aware. `dry_run=true` never sends the request; live execution requires `approval_granted=true`. Delivery uses bounded retry/backoff and stores final status, attempts, HTTP status and error evidence.

Secrets are referenced by environment-variable name; secret values are not persisted with connector configuration.

API:

```text
POST /api/v1/connectors
GET  /api/v1/connectors
GET  /api/v1/connectors/{id}
POST /api/v1/connectors/{id}/execute
```

Control Plane:

```text
http://localhost:3001/control-plane/connectors
```

## Cloud Reliability & SLO

V8 adds a deterministic SLO evaluator for release evidence plus a reusable HTTP load-smoke generator.

SLO evidence includes:

- availability
- p50 latency
- p95 latency
- p99 latency
- explicit PASS/FAIL against configured targets

API:

```text
POST /api/v1/operations/slo/evaluate
```

Load smoke:

```bash
python scripts/reliability/load_test.py \
  --base-url http://localhost:8000 \
  --requests 500 \
  --concurrency 25
```

Control Plane:

```text
http://localhost:3001/control-plane/operations
```

## Azure Production Path

V8 adds:

- `infra/azure/Pulumi.prod.yaml.example`
- a production deployment runbook
- a manually-triggered GitHub Actions Azure deployment workflow using OIDC
- a manually-triggered reliability smoke workflow

These assets make deployment repeatable. They do **not** claim a live Azure production deployment until real credentials are configured and `pulumi up` plus runtime/load validation succeeds.

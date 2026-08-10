# RedPA AI v4.1 — Persistent Control Plane Integration

v4.1 deepens three v4 domains together instead of adding more surface-area features:

1. Model Gateway Governance
2. Durable Workflow Control Plane
3. Event Delivery / DLQ / Replay

The v3 runtime remains the data plane. v4.1 adds durable governance and operational state around it.

## Model Gateway Governance

The Model Gateway can now enforce tenant provider allow-lists before invocation and record actual usage after a successful provider response.

Persistent tables:

- `platform_model_budgets`
- `platform_model_usage`

Capabilities:

- monthly token budgets;
- monthly cost budgets;
- tenant provider allow-lists;
- usage ledger by provider/model/request;
- optional pricing catalog through `MODEL_GATEWAY_PRICING_JSON`;
- Prometheus counters for denied requests, tokens, and recorded cost;
- transactional outbox events for budget changes and usage records.

Example pricing configuration:

```json
{
  "openai-compatible:gpt-4o-mini": {
    "input_per_1k": 0.00015,
    "output_per_1k": 0.0006
  },
  "ollama:*": {
    "input_per_1k": 0.0,
    "output_per_1k": 0.0
  }
}
```

A Model Gateway request may include `tenant_id`. When present, RedPA verifies tenant membership, checks governance before execution, restricts routed providers, then records actual usage.

## Workflow Control Plane

Persistent tables:

- `platform_workflow_definitions`
- `platform_workflow_runs`
- `platform_workflow_checkpoints`

Capabilities:

- versioned workflow definitions;
- durable run state;
- checkpoints with ordered sequence numbers;
- pause/resume/fail/cancel/complete transitions;
- retry attempt accounting;
- correlation IDs;
- output/error persistence;
- lifecycle events emitted through the transactional outbox;
- transition metrics.

The state machine intentionally prevents transitions out of terminal `completed` and `cancelled` states.

## Event Delivery Platform

The existing v3 `event_outbox` remains the source event record and Redis Streams publisher input.

v4.1 adds `platform_event_deliveries` for consumer delivery state:

- pending delivery;
- exponential retry scheduling;
- configurable maximum attempts;
- dead-letter state;
- replay count;
- replay by re-queuing the original outbox event;
- Prometheus failure, DLQ, replay, and DLQ-size metrics.

This keeps the transactional outbox as the reliability boundary instead of introducing a second competing event store.

## Migration

Run from `backend`:

```powershell
alembic upgrade head
```

The new migration is:

```text
p20v41a1b2c3_platform_v4_control_plane.py
```

and is chained after `p17a1b2c3d4e`.

## Main API additions

```text
GET/PUT  /api/v1/platform/model-governance/{tenant_id}
GET      /api/v1/platform/model-governance/{tenant_id}/usage
POST/GET /api/v1/platform/workflows/{tenant_id}/definitions
POST/GET /api/v1/platform/workflows/{tenant_id}/runs
POST     /api/v1/platform/workflows/{tenant_id}/runs/{run_id}/checkpoints
POST     /api/v1/platform/workflows/{tenant_id}/runs/{run_id}/transition
POST     /api/v1/platform/events/deliveries
POST     /api/v1/platform/events/deliveries/{delivery_id}/failed
POST     /api/v1/platform/events/deliveries/{delivery_id}/delivered
GET      /api/v1/platform/events/dead-letter
POST     /api/v1/platform/events/dead-letter/{delivery_id}/replay
```

## Verification

After applying the pack:

```powershell
python -m pytest backend/tests/test_platform_v4.py -q
python -m pytest backend/tests/test_platform_v4_1_integration.py -q
python -m pytest tests backend/tests -q
```

Then migrate the local Docker database and verify the API through Swagger before committing.

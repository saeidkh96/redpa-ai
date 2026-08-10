# RedPA AI v4 Platform Expansion

This expansion adds ten control-plane domains without replacing the existing v3 runtime. It is intentionally additive so each domain can be connected to durable persistence and distributed execution independently.

## Ten domains
1. Model Gateway Governance — tenant token/cost budgets and provider allow-lists.
2. Agent Registry & Runtime — versioned agent definitions, lifecycle state and capability discovery.
3. Tool/MCP Platform — tool catalog, role gates, approval requirements and sandbox profiles.
4. Durable Workflow Engine — versioned runs, checkpoints and explicit lifecycle transitions.
5. Enterprise Memory Platform — tenant policies, private/shared scopes and retention controls.
6. Evaluation Platform — benchmark runs with quality, latency and cost aggregation.
7. Enterprise Connectors — typed connector registry for REST, webhooks, GitHub, Jira, Slack, Confluence and email.
8. Policy & Approval Platform — versioned tenant policy rules and deny-by-default evaluation.
9. Event Platform — retry state, dead-letter queue and replay primitives.
10. Control Center — unified operational inventory across all nine domains.

## Architecture rule
The existing v3 services remain the data plane. `app/platform_v4` is the control-plane foundation. v4.1 has now moved Model Governance, Workflow Control, and Event Delivery into PostgreSQL-backed services, connected their mutations to the existing transactional outbox/Redis Streams boundary, and added Prometheus operational metrics. The remaining v4 domains can migrate from in-memory registries incrementally using the same pattern.

## API
Authenticated endpoints are mounted under `/api/v1/platform`. Start with `GET /api/v1/platform/overview`.

## Verification
Run `python -m pytest backend/tests/test_platform_v4.py -q` and `python -m pytest backend/tests/test_platform_v4_1_integration.py -q` from the repository root with the project virtual environment active. Then run `python -m pytest tests backend/tests -q` before committing.

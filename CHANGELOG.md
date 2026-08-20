## [19.3.0] - 2026-08-20

### Added

- Private Amazon RDS PostgreSQL managed data layer.
- Dedicated database subnets across two availability zones.
- ECS-to-RDS PostgreSQL security-group boundary.
- AWS Secrets Manager database connection metadata.
- ECS backend integration with managed PostgreSQL.
- Real AWS database validation and Alembic migration evidence.

### Validated

- Real ECS/Fargate to private RDS connection: PASS.
- PostgreSQL `SELECT 1`: PASS.
- Target database `redpa`: PASS.
- Alembic state: `v280a1b2c3d4e (head)`.
- Public schema table count: 48.
- ECS runtime remained healthy.
- Pulumi post-deployment drift check: 23 resources unchanged.

### Boundaries

- RDS is private and encrypted.
- Current RDS deployment is single-AZ.
- No production-grade high-availability claim is made.
## [19.2.0] - 2026-08-20

### Added

- Real AWS ECS/Fargate runtime deployment for the RedPA backend.
- Two public subnets across multiple availability zones.
- Internet Gateway and public routing for runtime validation.
- Dedicated ECS task execution role.
- Redis sidecar for middleware runtime dependencies.
- Pulumi-managed encrypted JWT runtime secret.
- CloudWatch runtime logging for backend and Redis containers.
- Immutable ECR image deployment using the `v19.2.0` tag.

### Validated

- ECS service `ACTIVE`.
- ECS rollout `COMPLETED`.
- Backend container `RUNNING / HEALTHY`.
- Redis container `RUNNING / HEALTHY`.
- Public `/api/v1/platform/live` validation: PASS.
- Public `/docs` validation: HTTP 200.
- CloudWatch runtime logs: PASS.
- Pulumi post-deployment preview: 16 resources unchanged.

### Boundaries

- Runtime environment remains `development`.
- PostgreSQL is not yet connected to a managed AWS database.
- Deep readiness is not claimed.
- Direct port `8000` exposure is temporary runtime-validation ingress.
- Production HTTPS / ALB ingress is not yet claimed.
## [19.1.0] - 2026-08-20

### Added

- Real AWS development foundation deployment using Pulumi in `eu-central-1`.
- AWS VPC, ECS cluster, ECR repository, and CloudWatch log group deployment validation.
- Least-privilege AWS deployment policy for the V19.1 infrastructure foundation.
- Microsoft governed approval integration boundary with persistent human-review state.
- Authenticated approval decision callback with pending-to-approved lifecycle validation.
- PostgreSQL-backed approval persistence validated across backend restart.
- V19.1 enterprise governance analytics API and service.
- V19.1 release finalization and production-validation tests.

### Validated

- AWS Pulumi foundation deployment: PASS.
- Pulumi post-deployment preview: no infrastructure changes.
- Microsoft governed approval persistence: PASS.
- Authenticated approval callback: PASS.
- Backend restart persistence: PASS.
- Governance analytics targeted validation: PASS.
- Full regression baseline prior to release finalization: 437 tests passed.
- Secret scan: PASS.
- Alembic database migration state: `v280a1b2c3d4e (head)`.

### Boundaries

- AWS foundation deployment does not claim that the complete RedPA application workload is publicly running on ECS.
- Microsoft integration provides a Power-Automate-compatible governed approval boundary; no live Microsoft tenant connection is claimed.
- No Microsoft credentials are embedded in the repository.

## [19.0.0] - 2026-08-20

### Added
- V18.3 PostgreSQL-backed Control Plane agent run history and summary aggregation.
- V18.3 persisted trace, fallback, latency, and evaluation evidence.
- V18.4 credential-free Power Automate approval integration contract with an explicit human-approval boundary.
- V18.4 Copilot Studio REST action contracts for platform, agent, and incident summaries.
- V18.5 enterprise analytics APIs for operational KPIs, Power BI-friendly JSON, and Excel-compatible CSV export.
- V18.5 analytics backed by persisted V18.3 execution history.
- V19 AWS Pulumi deployment foundation for VPC, ECS, ECR, and CloudWatch.
- Control Plane views for Run History, Microsoft integration readiness, and Enterprise BI.

### Changed
- Release identity synchronized across backend, Ops Agent, frontend, Python SDK, Helm, Compose, and CI to `19.0.0`.
- Alembic head advanced to `v280a1b2c3d4e`.

### Validation
- 425 automated tests passing.
- V18.3 runtime persistence validation: PASS.
- V18.4 Microsoft integration contract validation: PASS.
- V18.5 enterprise analytics E2E validation: PASS.
- V19 AWS `pulumi preview`: PASS.
- Microsoft integration remains contract/readiness based; no live tenant integration is claimed.
- AWS resources have not been deployed; `pulumi up` has not been run.

## [18.2.0] - 2026-08-19

### Added
- Production E2E demonstration across the RedPA multi-agent runtime.
- Controlled primary-agent failure injection and self-healing fallback.
- Real A2A fallback execution through the shipped remote-agent runtime.
- Trusted-agent and governance boundaries in the E2E demonstration.
- Recovery/rejoin validation and V16 continuous evaluation integration.
- Machine-readable E2E audit evidence.
- Production E2E Control Plane view.

### Changed
- Release identity synchronized across backend, Ops Agent, frontend, Python SDK, Helm, Compose, and CI to `18.2.0`.

### Validation
- 420 automated tests passing.
- V18.2 Production E2E Demo: 10/10 stages PASS.
- Alembic head remains `v270a1b2c3d4e`.

## [11.0.0] - 2026-08-17

### Added

- V11 autonomous reliability evaluation with persisted evidence.
- V12 health-aware multi-agent failover.
- V13 adaptive governance recommendations with `auto_applied=false`.
- V14 compliance evidence completeness checks.
- V15 production-cloud readiness scoring.
- V16 continuous evaluation and rollout decision gate.
- V17 enterprise connector governance and approval assessment.
- V18 trusted agent registry semantics.
- Shared `platform_evolution_records` persistence.
- Platform Evolution API.
- Platform Evolution Control Plane page.
- V11-V18 CI contract gate.

### Changed

- Product release version advanced to `11.0.0`.
- Backend, Ops Agent, frontend, Python SDK, Helm, Compose, and CI release metadata aligned to `11.0.0`.
- Control Plane expanded from V10 governance/policy visibility to platform evolution evidence.

### Verified

- 359 Python tests passed.
- Alembic migration chain advanced successfully to `v180a1b2c3d4e`.
- Eight live Platform Evolution records were persisted and displayed in the Control Plane.
- V11 reliability returned `action_required`.
- V12 failover returned `routable`.
- V13 adaptive governance returned `recommendation`.
- V14 compliance correctly identified missing evidence.
- V15 cloud readiness returned `ready` with score `0.8`.
- V16 rollout decision returned `PROMOTE`.
- V17 connector assessment returned `review` with effective approval required.
- V18 agent registration returned `trusted`.
- V10.3 automated governed recovery remained operational.


## [10.0.0] - 2026-08-16

### Added
- Persistent V10 governed agent runs and execution-event tracing.
- Governance API and runtime orchestration integration.
- Explicit Human-in-the-Loop lifecycle resume for blocked runs.
- Governed autonomous-operations integration with diagnosis, policy, remediation, recovery verification, and evaluation.
- Dedicated Spring Boot Policy Service in the primary Docker Compose stack.
- V10 governance, runtime, Ops, lifecycle, and release-hardening CI gates.

### Changed
- Promoted governance from tool-boundary enforcement to a persisted runtime lifecycle.
- Integrated policy decisions and evaluation metadata with governed runs.
- Updated backend, frontend, SDK, Helm, Compose, CI, and environment version contracts to `10.0.0`.
- Hardened OpenTelemetry Collector and Tempo startup/restart behavior.
- Operations remediation now resumes an approved blocked run before executing the side effect.

### Fixed
- Fixed the V10 lifecycle path where a blocked run could not correctly continue to completion after valid approval.
- Separated physical recovery failure from governance-finalization failure in Ops tracing.

### Verified
- 344 Python tests passed.
- Frontend production build passed.
- Primary Docker Compose stack validated and started successfully.
- Backend and Ops Agent reported version `10.0.0`; Policy Service reported `UP`.
- End-to-end governed recovery completed with evaluation score `1.0`.


# Changelog

## V9.0.0 Ã¢â‚¬â€ Production Cloud & Autonomous Operations

- added persisted incident and remediation action records;
- added Docker-backed V9 Ops Agent with explicit approval and stateful-service denylist;
- added incident diagnosis and approval-gated stateless restart;
- added release-readiness gate combining SLO, incidents, security and regression evidence;
- added cloud cost estimator;
- added PostgreSQL backup and explicitly confirmed restore tooling;
- added V9 incidents, release gate and cloud cost Control Plane views;
- added V9 Alembic migration and contract tests;
- aligned application, frontend, SDK, Helm and CI release metadata to `9.0.0`.

## V8.0.0 Ã¢â‚¬â€ Enterprise AI Operations & Automation

- added generic analytics fact ingestion and KPI query engine with weighted aggregation;
- added JSONB dimensional slicing and metric/dimension catalog discovery;
- added Analytics Control Plane workspace;
- added persisted enterprise connector registry and delivery audit state;
- added Webhook, Slack Webhook, GitHub Dispatch and n8n connector kinds;
- added dry-run, explicit approval, retries and environment-based secret indirection for external side effects;
- added Connectors Control Plane workspace;
- added deterministic SLO evaluation and reusable HTTP load-smoke evidence generator;
- added Operations/SLO Control Plane workspace;
- added Azure production stack example, runbook and manual OIDC deployment workflow;
- added manual GitHub Actions reliability smoke workflow with artifact upload;
- expanded sync/async SDK and CLI operations;
- aligned current release metadata to `8.0.0`.

## V7.0.0 Ã¢â‚¬â€ Enterprise Research

- added persisted enterprise research runs and timeline events;
- added background evidence-first execution using the existing Research Agent;
- added deterministic coverage/source-diversity quality scoring;
- added provenance-preserving Markdown research reports;
- added `/api/v1/research/runs` create/list/detail APIs;
- added live `/control-plane/research` workspace;
- added sync/async SDK research operations and `redpa research` CLI commands;
- added V7 Alembic persistence and regression/contract tests;
- aligned backend, Docker, frontend, SDK and Helm application metadata to `7.0.0`.

## V6.0.0 Ã¢â‚¬â€ Developer Platform

### Completed V6 surface

- added synchronous and asynchronous Python SDK clients;
- added durable-workflow operations;
- added Human Review operations;
- added MCP discovery and execution operations;
- added benchmark-suite and reliability-history client access;
- added SDK examples and package-build support;
- added dedicated SDK CI across Python 3.11, 3.12 and 3.13;
- promoted SDK package version to `6.0.0`.

### Batch 1

- added installable `redpa-ai-sdk` Python package;
- added `RedPA` client with token/config handling and typed core responses;
- added `redpa` CLI;
- added status and doctor commands;
- added agent discovery, provider, tool, reliability, release-gate, and candidate-report commands;
- added SDK contract and HTTP mock tests.


## V5.5.0 Ã¢â‚¬â€ Evaluation & Reliability

### Batch 4

- added persisted benchmark suite registry and reusable evaluation corpora;
- added persisted suite execution through the evaluation API;
- added provider reliability snapshot history;
- added release candidate evidence reports combining evaluation, gate, benchmark, and reliability state;
- extended the V5.5 Control Plane with suite, reliability-history, and candidate-report views.

### Batch 3

- added persisted release quality-gate history;
- added release labels and gate metadata;
- added CI-friendly release gate endpoint with HTTP 409 on blocked promotion;
- added persisted benchmark trend endpoint;
- added release gate and quality-trend views to the V5.5 Control Plane;
- added `scripts/quality/release_gate.py` for CI process exit codes.

### Batch 2

- persisted benchmark runs and case-level results;
- added benchmark history filtered by agent/model;
- added provider reliability scorecards from health + circuit state;
- added deterministic retry/fallback failure validation;
- extended the V5.5 Control Plane with benchmark history and provider reliability.

### Batch 1

- added persisted baseline/candidate evaluation comparison;
- added aggregate and per-metric regression detection;
- added missing-candidate-metric regression detection;
- added configurable evaluation quality gates;
- added minimum-score and candidate pass-threshold checks;
- added `/control-plane/reliability` for baseline/candidate inspection.


## V5.0.0 Ã¢â‚¬â€ Control Plane

### Added

- unified Next.js Control Plane under `/control-plane`;
- operational views for agents, model providers, Tools & MCP, durable workflows and Human Reviews;
- Execution Explorer backed by persisted distributed-agent workflow/subtask state;
- Agent Memory analytics and semantic-search console;
- tenant Usage & Cost console backed by Platform V4 model-governance accounting;
- integrated Governance view for policy enforcement and policy audit;
- Access & Tenancy view for tenant workspaces and configured OAuth providers;
- V5 Control Plane architecture and release documentation.

### Design constraint

The V5 Control Plane only surfaces capabilities backed by existing repository APIs and persisted services. It does not label roadmap or placeholder functionality as implemented.

## v4.2 Production Agentic Systems Readiness

- Added OpenAI, Anthropic Claude, Gemini, and Ollama multi-provider gateway support.
- Added cost-aware capability routing and provider economics catalog.
- Added unified production agent runtime for LLMs, guarded tools, data context, and business rules.
- Added deterministic input/output guardrails, evaluation gates, AI-specific Prometheus telemetry, concurrency/idempotency/retry foundations.
- Added `/api/v1/production-ai` readiness and runtime execution APIs.


## v4.1 Control Plane Integration

### Added

- persistent tenant model budgets and model usage ledger;
- provider allow-list enforcement in the existing Model Gateway;
- configurable per-provider/model pricing for token cost accounting;
- persistent workflow definitions, runs, checkpoints, and lifecycle transitions;
- workflow lifecycle events through the existing transactional outbox;
- event delivery state with exponential retry, dead-letter queue, and replay;
- Prometheus metrics for governance, workflows, and delivery failures;
- authenticated v4.1 control-plane APIs and tenant membership checks.

## v1.0.0

### Added

- FastAPI platform architecture;
- JWT authentication;
- conversations and messages;
- Planner, Chat, RAG, Tool, and Human Review workflows;
- MCP servers and unified tool execution;
- A2A coordinator and specialist agents;
- distributed durable workflow persistence and resume;
- PostgreSQL and Qdrant Agent Memory;
- shared Agent context;
- memory summarization, deduplication, and retention;
- Redis cache, rate limiting, and idempotency;
- Worker, Scheduler, retries, and dead-letter jobs;
- Prometheus and Grafana monitoring;
- OpenTelemetry and Tempo tracing;
- security headers and production validation;
- structured JSON logging;
- request IDs, correlation IDs, and error IDs;
- standardized error responses;
- readiness, liveness, and dependency health;
- request and SQL performance monitoring;
- Docker Compose;
- Kubernetes and Helm deployment resources.

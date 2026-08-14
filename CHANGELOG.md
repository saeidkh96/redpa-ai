# Changelog

## V8.0.0 — Enterprise AI Operations & Automation

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

## V7.0.0 — Enterprise Research

- added persisted enterprise research runs and timeline events;
- added background evidence-first execution using the existing Research Agent;
- added deterministic coverage/source-diversity quality scoring;
- added provenance-preserving Markdown research reports;
- added `/api/v1/research/runs` create/list/detail APIs;
- added live `/control-plane/research` workspace;
- added sync/async SDK research operations and `redpa research` CLI commands;
- added V7 Alembic persistence and regression/contract tests;
- aligned backend, Docker, frontend, SDK and Helm application metadata to `7.0.0`.

## V6.0.0 — Developer Platform

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


## V5.5.0 — Evaluation & Reliability

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


## V5.0.0 — Control Plane

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

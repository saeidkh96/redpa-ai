# Changelog

## V5.5.0 — Evaluation & Reliability (in progress)

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

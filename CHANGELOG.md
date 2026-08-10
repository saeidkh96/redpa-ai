# Changelog

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

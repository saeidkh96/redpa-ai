# RedPA AI V8.0 — arc42 Architecture Documentation

## 1. Introduction and Goals

RedPA AI is a developer-facing Agentic AI platform coordinating models, agents, tools, retrieval, durable workflows, policy enforcement, Human-in-the-Loop, semantic memory, evaluation, event delivery, and observability.

Primary quality goals:

1. Safety and governed side effects
2. Reliability and resumable execution
3. Auditability
4. Extensibility
5. Observability
6. Testability
7. Tenant-aware operation
8. Developer usability

## 2. Constraints

- Python / FastAPI is the primary platform backend.
- Java / Spring Boot provides the dedicated policy microservice.
- PostgreSQL is the primary relational persistence layer.
- Qdrant provides vector retrieval for RAG and semantic memory.
- Redis provides runtime coordination, caching, background-job support, and Redis Streams.
- Docker Compose is the primary local integration runtime.
- Existing API and workflow contracts must remain regression-tested as the architecture evolves.

## 3. Context and Scope

External actors and systems include:

- API consumers;
- developers using the Python SDK and `redpa` CLI;
- operators using the Next.js Control Plane;
- model providers;
- MCP servers and external tools;
- GitHub and other external integrations;
- deployment and observability infrastructure.

See [`c4.md`](c4.md) for system and container views.

## 4. Solution Strategy

RedPA combines:

- bounded contexts and service-oriented modularization;
- stateful agent orchestration;
- durable distributed workflows;
- policy and guardrail gates;
- Human-in-the-Loop continuation;
- MCP tool interoperability;
- A2A specialist delegation;
- model-provider abstraction and reliability controls;
- semantic retrieval and memory;
- tenant-aware access foundations;
- transactional outbox and Redis Streams;
- evaluation, benchmarking, reliability snapshots, and release quality gates;
- metrics, logs, traces, and health signals;
- SDK/CLI clients over stable platform APIs.

## 5. Building Block View

Main building blocks:

- Developer Platform — Python SDK, async client, CLI, examples
- Control Plane — Next.js operator UI
- Platform API — FastAPI V1 routers
- Identity & Access — authentication, tenancy, memberships, OAuth foundations
- Agent Runtime — planner, RAG, research, tools, specialist and remote agents
- Durable Execution — workflows, checkpoints, retries, resume
- Human Oversight — review, approve/reject, gated resume
- MCP Platform — filesystem, GitHub, PostgreSQL, Docker MCP services
- A2A Runtime — coordinator and specialist agents
- Model Gateway — provider abstraction, routing, economics, reliability
- Evaluation & Release Quality — evaluations, benchmarks, regression and release gates
- Policy & Governance — guardrails, Spring policy service, audit
- Event Runtime — transactional outbox, publisher, Redis Streams
- Persistence — PostgreSQL, Qdrant, Redis
- Operations — background worker, scheduler, metrics, tracing, performance
- Observability — Prometheus, Grafana, OpenTelemetry Collector, Tempo

## 6. Runtime Views

### Agent/tool execution

```text
Client / SDK / Control Plane
  -> FastAPI
  -> Planner / Agent Runtime
  -> Guardrails + Policy
  -> ALLOW / REVIEW / DENY
  -> Internal Tool / MCP / A2A specialist
  -> Persist state + audit + telemetry
```

### Durable Human Review

```text
Workflow
  -> risky or approval-gated operation
  -> Human Review
  -> approve / reject
  -> resume or stop
  -> persisted workflow state
```

### Model execution

```text
Agent
  -> Model Gateway
  -> provider/routing decision
  -> reliability / retry / fallback controls
  -> provider
  -> normalized result + usage/reliability evidence
```

### Event publication

```text
Application transaction
  -> Transactional Outbox
  -> Outbox Publisher
  -> Redis Streams
  -> future/external consumers
```

### Release quality

```text
Evaluation / Benchmark evidence
  -> regression comparison
  -> reliability evidence
  -> release quality gate
  -> PASS / FAIL + persisted report
```

## 7. Deployment View

The local integration runtime uses `docker-compose.yml` plus `docker-compose.phase13.yml`.

The main stack contains backend, frontend, PostgreSQL, Qdrant, Redis, background worker/scheduler, outbox publisher, four MCP services, A2A coordinator, five specialist agents, Prometheus, Grafana, OpenTelemetry Collector, and Tempo. The phase-13 compose overlay adds the Spring Boot policy service and wires the backend to it.

Kubernetes/Helm and Azure/Pulumi are deployment/reference assets. A live production cluster or Azure deployment is not claimed solely from repository configuration.

## 8. Cross-Cutting Concepts

- JWT authentication
- tenant/workspace boundaries and membership roles
- OAuth provider discovery and PKCE foundations
- structured errors
- request/correlation/trace identifiers
- policy decisions and audit events
- idempotency
- retries, fallback and circuit breakers
- rate limiting
- schema validation
- secret scanning
- Prometheus metrics
- OpenTelemetry traces
- release-quality validation

## 9. Architecture Decisions

See [`adr/`](adr/).

## 10. Quality Requirements

The architecture should support:

- policy enforcement before sensitive side effects;
- durable and resumable workflows;
- Human Review for approval-gated operations;
- replaceable model providers;
- authenticated operational APIs;
- tenant-aware access foundations;
- observable distributed execution;
- deterministic tests for high-risk decisions;
- release regression detection;
- developer access without duplicating server-side logic.

## 11. Risks and Technical Debt

- Some Python modules retain historical layering and can be incrementally consolidated.
- Production OAuth token exchange/account linking still requires real provider credentials and persistent callback/state handling.
- Tenant authorization can be expanded beyond the current RBAC/isolation foundations.
- External event consumers/connectors remain an expansion area.
- Azure/Pulumi and Kubernetes/Helm require environment-specific deployment validation before production claims.
- Larger-scale load, chaos, and resilience validation remains future work.
- Cross-service contracts should continue to be explicitly versioned as the platform grows.

## 12. Glossary

**A2A** — Agent-to-Agent communication.

**MCP** — Model Context Protocol.

**HITL** — Human-in-the-Loop.

**RBAC** — Role-Based Access Control.

**Transactional Outbox** — persistence pattern used to coordinate application state changes with reliable event publication.

**Policy Decision** — `ALLOW`, `REVIEW`, or `DENY` result produced by governance rules.

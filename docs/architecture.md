# RedPA AI v9.0.0 Architecture

This document is the concise architecture entry point for the V8 source tree. Detailed views are maintained in:

- [`architecture/c4.md`](architecture/c4.md)
- [`architecture/arc42.md`](architecture/arc42.md)
- [`architecture/ddd.md`](architecture/ddd.md)
- [`architecture/adr/`](architecture/adr/)

![RedPA AI core platform architecture](images/architecture.png)

## Runtime Topology

The validated local integration environment is composed from `docker-compose.yml` and `docker-compose.phase13.yml`.

### Entry points

- FastAPI backend — `:8000`
- Next.js Control Plane — `:3001`
- Python SDK and `redpa` CLI — HTTP clients of the backend API

### Core runtime

- planner/agent runtime, RAG, research and tool workflows;
- distributed durable workflows with checkpoint/resume behavior;
- Human Review approval/rejection and gated continuation;
- Agent Memory and semantic retrieval;
- Model Gateway, usage/economics and reliability controls;
- evaluation, benchmarks, regression analysis and release quality gates;
- authentication, tenancy/RBAC foundations and OAuth provider/PKCE foundations;
- guardrails and policy enforcement;
- transactional outbox and event APIs.

### Policy boundary

`docker-compose.phase13.yml` adds the Spring Boot Policy Service on `:8090` and configures the backend to call it for policy decisions.

### MCP tool plane

The main Docker Compose stack contains four MCP services:

- Filesystem MCP — `:8010`
- GitHub MCP — `:8020`
- PostgreSQL MCP — `:8030`
- Docker MCP — `:8040`

MCP is the tool-interoperability boundary: server registration/health, tool discovery, structured arguments, qualified execution, and policy/Human Review integration.

### A2A agent plane

The distributed agent topology contains:

- A2A Coordinator — `:8050`
- Research Agent — `:8061`
- PostgreSQL Agent — `:8062`
- Docker Agent — `:8063`
- Filesystem Agent — `:8064`
- GitHub Agent — `:8065`

A2A is the agent-delegation boundary: capability discovery, specialist selection, distributed subtasks, parallel execution, and result aggregation.

### Background and event runtime

- Background Worker
- Background Scheduler
- Outbox Publisher
- Redis-backed runtime coordination
- Redis Streams event publication

### Persistence

- PostgreSQL — transactional and relational platform state
- Qdrant — vector retrieval for RAG and semantic memory
- Redis — caching, runtime coordination and event streams

### Observability

- Prometheus — metrics
- Grafana — dashboards
- OpenTelemetry Collector — trace collection
- Tempo — distributed trace storage/query path
- structured application logging and correlation identifiers

## Developer Platform Boundary

V6 adds an installable Python SDK, asynchronous client, CLI, examples, package build configuration, and dedicated SDK CI. These are clients of the platform API; orchestration, durable state, policy, and governance remain server-side.

## Deployment Boundary

Docker Compose is the local integration runtime validated during the V6 release process. Kubernetes/Helm and Azure/Pulumi are deployment/reference assets. Their presence in the repository does not by itself establish a live production deployment.

## Release Identity

V6 release metadata is aligned to `6.0.0` across the FastAPI application default, Docker runtime, Next.js package, Python SDK, and Helm `appVersion`.


## V7 Enterprise Research Application Layer

V7 introduces a persisted application workflow above the existing platform primitives.

```text
Control Plane / SDK / CLI
        |
        v
/api/v1/research/runs
        |
        v
EnterpriseResearchService
        |
        +--> ResearchAgentService --> DDGS web retrieval
        +--> ResearchQualityEvaluator
        +--> EnterpriseResearchReportBuilder
        |
        v
PostgreSQL
  enterprise_research_runs
  enterprise_research_events
```

The V7 workspace uses the existing Research Agent rather than duplicating web retrieval. Its execution timeline is persisted and surfaced through polling in the Control Plane.


## V8 Enterprise Operations Layer

V8 composes three operator-facing capabilities above the core platform:

```text
Analytics facts -> KPI Engine -> dimensional/weighted queries -> Analytics Control Plane
Connector registry -> approval/dry-run -> outbound delivery/retry -> delivery audit
Load evidence -> SLO evaluator -> PASS/FAIL release evidence -> Operations Control Plane
```

The Azure/Pulumi production path remains infrastructure-as-code until a real subscription deployment is completed and validated.

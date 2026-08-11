<p align="center">
  <img src="docs/images/logo.png" width="220" alt="RedPA AI">
</p>

<h1 align="center">RedPA AI</h1>

<p align="center">
  <strong>Production-Oriented Enterprise Agentic AI Platform</strong>
</p>

<p align="center">
  Multi-agent orchestration · Model Gateway · MCP · A2A · RAG · Durable Workflows ·
  Human-in-the-Loop · Agent Memory · Policy Enforcement · Evaluation · Observability
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.140-009688" alt="FastAPI">
  <img src="https://img.shields.io/badge/LangGraph-1.2-black" alt="LangGraph">
  <img src="https://img.shields.io/badge/PostgreSQL-17-336791" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Qdrant-Vector_DB-red" alt="Qdrant">
  <img src="https://img.shields.io/badge/Redis-Streams-DC382D" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED" alt="Docker">
  <img src="https://img.shields.io/badge/Kubernetes-Helm-326CE5" alt="Kubernetes">
  <img src="https://img.shields.io/badge/Azure-Pulumi-0078D4" alt="Azure">
  <img src="https://img.shields.io/badge/Release-v4.2-success" alt="Release">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

RedPA AI is an open-source platform for building and operating **agentic AI systems** with explicit orchestration, tool execution, model routing, policy controls, human approval, durable state, memory, evaluation, and production observability.

Rather than exposing a single LLM behind an API, RedPA separates the major concerns of an agentic system into independent subsystems: agents, model providers, tools, MCP servers, distributed agents, workflows, policy, memory, events, identity, telemetry, and infrastructure.

The current **V4.2** implementation extends this architecture with a production-agent runtime, multi-provider model gateway, cost-aware routing, runtime guardrails, evaluation gates, reliability controls, and AI-specific telemetry.

---

## Architecture

```text
Clients / API Consumers
        │
        ▼
FastAPI API Layer (/api/v1)
        │
        ├── Authentication / OAuth
        ├── Tenant / RBAC
        └── Conversations / Messages
        │
        ▼
Agentic Orchestration
        │
        ├── Planner / Chat / RAG / Research
        ├── Tool Execution
        ├── A2A Delegation
        └── Human Review
        │
        ├───────────────┬────────────────┐
        ▼               ▼                ▼
Production Agent    Durable          Agent Memory
Runtime             Workflows
        │
        ├── Guardrails
        ├── Evaluation
        ├── Idempotency
        ├── Concurrency
        └── Runtime Telemetry
        │
        ▼
Model Gateway
        │
        ├── Explicit Routing
        ├── Agent Routing
        ├── Capability Routing
        ├── Cost-Aware Routing
        ├── Fallback
        └── Reliability
        │
        ├── Ollama
        ├── Anthropic
        ├── Gemini
        └── OpenAI-Compatible
        │
        ▼
Tool Platform / MCP
        │
        ▼
Distributed / Specialist Agents
        │
        ▼
Governance & Safety
Policy / Guardrails / Evaluation / HITL
        │
        ▼
PostgreSQL / Qdrant / Redis Streams
        │
        ▼
Prometheus / Grafana / OpenTelemetry / Tempo
```

---

## V4.2 — Production Agentic Systems Readiness

V4.2 focuses on the runtime layer required to operate agentic workloads with stronger routing, reliability, safety, evaluation, and cost controls.

### Production Agent Runtime

`ProductionAgentRuntime` provides a unified execution path for agent workloads.

The implemented runtime can combine:

- agent identity;
- user prompts;
- business rules;
- retrieved/data context;
- tool execution results;
- model-gateway invocation;
- input and output guardrails;
- runtime evaluation;
- latency and cost budgets;
- idempotent execution;
- concurrency control;
- AI-specific telemetry.

The runtime returns structured execution metadata including provider, model, latency, token usage, estimated cost, attempted providers, guardrail results, evaluation result, tool results, and cache state.

---

## Multi-Provider Model Gateway

RedPA includes a provider-independent model gateway.

Implemented provider adapters include:

- **Ollama**
- **Anthropic**
- **Google Gemini**
- **OpenAI-compatible APIs**
- **Mock provider** for testing

The gateway separates model consumers from provider-specific implementations.

### Routing

The routing layer supports:

- explicit provider selection;
- per-agent provider/model routes;
- capability-aware routing;
- cost-aware routing;
- configurable fallback providers.

Cost-aware routing uses a configurable model-economics catalog and estimated token usage to rank compatible providers.

Provider economics can be supplied through `MODEL_GATEWAY_ECONOMICS_JSON` and agent-specific routes through `MODEL_GATEWAY_AGENT_ROUTES_JSON`.

---

## Reliability Controls

Implemented controls include:

- provider fallback;
- retry handling;
- circuit-breaker support;
- concurrency limiting;
- idempotency handling;
- durable workflow persistence and resume;
- background job execution;
- external HTTP resilience.

These mechanisms are implemented across the model gateway, production runtime, middleware, clients, and durable-workflow subsystems.

---

## Runtime Guardrails

V4.2 includes deterministic input and output guardrails.

The current production guardrail pipeline implements:

- email-address redaction;
- common secret/token pattern redaction;
- prompt-injection pattern detection;
- `ALLOW`;
- `REDACT`;
- `REVIEW`;
- `BLOCK` decision types.

Input guardrails execute before model invocation and output guardrails execute before the final runtime result is returned.

---

## Runtime Evaluation

Agent outputs pass through a runtime evaluation gate.

Implemented outcomes are:

- `PASS`
- `RETRY`
- `HUMAN_REVIEW`
- `BLOCK`

Evaluation currently considers empty responses, latency budgets, cost budgets, severity of budget violations, and evaluation score thresholds.

---

## Agentic Orchestration

RedPA uses LangGraph-based orchestration for agent execution.

The agent graph contains dedicated nodes for:

- planning;
- conversational execution;
- Retrieval-Augmented Generation;
- research;
- tool execution;
- Agent-to-Agent delegation;
- Human Review;
- capability-unavailable handling;
- response generation.

Planner routing determines which execution path should handle a request.

---

## Retrieval-Augmented Generation

The platform includes document and retrieval infrastructure backed by PostgreSQL and Qdrant.

Implemented components include:

- document APIs;
- document persistence;
- document chunks;
- document content storage;
- vector retrieval infrastructure;
- RAG agent execution;
- semantic context integration.

---

## Model Context Protocol

RedPA contains an MCP client, registry, manager, catalog, configuration loader, permission layer, caching, naming, planner intent handling, and tool formatting.

Implemented MCP server integrations include:

- **Filesystem**
- **PostgreSQL**
- **GitHub**
- **Docker**

The platform includes dedicated security controls for filesystem, PostgreSQL, and Docker MCP execution.

---

## Unified Tool Execution

Internal and MCP tools are exposed through a unified tool layer integrating tool discovery, execution, permissions, policy enforcement, metrics, and formatting.

---

## Agent-to-Agent Communication

The repository includes:

- A2A schemas;
- agent registry;
- built-in agents;
- A2A service;
- protocol cards;
- coordinator;
- executor;
- specialist routing;
- specialist execution;
- remote agent registry;
- remote A2A client;
- distributed multi-agent services.

The Docker environment also defines specialist agent services including PostgreSQL, Docker, Filesystem, GitHub, Research, and an A2A coordinator.

---

## Multi-Agent Execution

Implemented areas include:

- multi-agent schemas;
- multi-agent execution service;
- distributed multi-agent execution;
- multi-agent metrics;
- multi-agent policy controls;
- specialist routing.

---

## Durable Workflows

Implemented functionality includes:

- workflow persistence;
- durable state;
- workflow metadata;
- execution resume;
- distributed durable workflow services;
- background workers;
- scheduler support.

---

## Human-in-the-Loop

The system supports:

- creation of review requests;
- persisted review state;
- approve/reject decisions;
- integration with agent execution;
- workflow resume after review.

---

## Agent Memory

Implemented modules include:

- memory repository;
- memory service;
- semantic memory;
- context handling;
- memory injection;
- lifecycle hooks;
- maintenance;
- analytics;
- administration APIs;
- dashboard APIs.

---

## Policy Enforcement

The platform includes:

- policy evaluation;
- guarded execution;
- tool-boundary enforcement;
- MCP-boundary enforcement;
- policy audit events;
- policy metrics;
- Human Review integration.

A dedicated policy service is included in the repository alongside the main Python backend.

---

## Identity, RBAC and Multi-Tenancy

Implemented areas include:

- JWT authentication;
- users;
- tenants;
- tenant memberships;
- role-based access control;
- tenant-scoped operations;
- OAuth provider infrastructure;
- OAuth identity persistence;
- PKCE-related OAuth support.

Tenant-aware controls are also integrated into production AI/model governance paths.

---

## Events and Background Processing

RedPA includes event-driven infrastructure built around a transactional outbox and Redis Streams.

Implemented components include:

- event contracts;
- persistent event outbox;
- outbox publisher;
- Redis Streams event bus;
- event APIs;
- background workers;
- background scheduler;
- heartbeat/job infrastructure.

---

## Observability

The local stack includes:

- **Prometheus**
- **Grafana**
- **OpenTelemetry Collector**
- **Grafana Tempo**
- structured application logging;
- correlation IDs;
- trace context propagation;
- health endpoints;
- performance monitoring.

### V4.2 AI Runtime Metrics

The production runtime records metrics for:

- agent execution outcomes;
- runtime latency;
- estimated model cost;
- guardrail decisions;
- tool-call outcomes.

---

## API Surface

The FastAPI application exposes versioned APIs under `/api/v1`.

Implemented API areas include health, platform health, authentication, OAuth, users, tenants, conversations, messages, chat, LLM, documents, agents, multi-agents, distributed agents, remote agents, MCP, tools, unified tools, human reviews, durable workflows, agent memory, evaluations, model gateway, guardrails, policy enforcement, events, background jobs, performance, monitoring, production AI, and platform V4 controls.

Interactive OpenAPI documentation is available at:

```text
http://localhost:8000/docs
```

when the backend is running locally.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Agent Orchestration | LangGraph |
| Validation / Configuration | Pydantic |
| Database | PostgreSQL |
| Vector Database | Qdrant |
| Messaging | Redis / Redis Streams |
| Model Providers | Ollama, Anthropic, Gemini, OpenAI-compatible |
| Tool Protocol | MCP |
| Agent Communication | A2A |
| Policy Service | Spring Boot |
| Frontend | Next.js |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Tracing | OpenTelemetry, Tempo |
| Containers | Docker, Docker Compose |
| Orchestration | Kubernetes, Helm |
| Cloud Infrastructure | Azure, Pulumi |
| CI/CD | GitHub Actions |

---

## Repository Structure

```text
redpa-ai/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── a2a/
│   │   ├── a2a_multi/
│   │   ├── a2a_protocol/
│   │   ├── a2a_remote/
│   │   ├── agent_memory/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── architecture/
│   │   ├── auth/
│   │   ├── background_jobs/
│   │   ├── clients/
│   │   ├── core/
│   │   ├── database/
│   │   ├── distributed_durable/
│   │   ├── distributed_multi/
│   │   ├── evaluation/
│   │   ├── events/
│   │   ├── guardrails/
│   │   ├── mcp/
│   │   ├── mcp_servers/
│   │   ├── middleware/
│   │   ├── model_gateway/
│   │   ├── monitoring/
│   │   ├── observability/
│   │   ├── performance/
│   │   ├── platform_v4/
│   │   ├── production_ai/
│   │   ├── services/
│   │   └── main.py
│   └── config/
├── frontend/
├── policy-service/
├── deploy/
│   ├── helm/
│   └── kubernetes/
├── infra/
│   └── azure/
├── monitoring/
├── observability/
├── docs/
├── tests/
├── .github/
│   └── workflows/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone

```bash
git clone <repository-url>
cd redpa-ai
```

### 2. Configure environment

At minimum, configure backend values such as:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai
JWT_SECRET_KEY=replace-with-a-secure-secret
```

Add provider-specific configuration depending on the model providers you intend to use.

### 3. Start the stack

```bash
docker compose up --build
```

### 4. Local services

```text
Backend API       http://localhost:8000
OpenAPI           http://localhost:8000/docs
Frontend          http://localhost:3001
Grafana           http://localhost:3000
Prometheus        http://localhost:9090
Tempo             http://localhost:3200
```

---

## Running Tests

```bash
python -m pytest tests -q
```

The repository contains automated tests covering major platform areas including model gateway, provider adapters, routing, reliability, MCP, A2A, distributed agents, durable workflows, agent memory, guardrails, policy enforcement, evaluations, tenant isolation, RBAC, OAuth, events, production security, architecture contracts, cloud architecture, platform health, and performance monitoring.

---

## Deployment Assets

The repository contains deployment assets for Docker, Kubernetes, Helm, and Azure/Pulumi.

These assets provide deployment infrastructure; their presence does **not** imply that a public production RedPA deployment is currently running.

---

## CI/CD and Release Engineering

GitHub Actions workflows are included for continuous integration, security checks, release workflows, release gates, and Azure Pulumi previews.

---

## Security

Implemented areas include:

- JWT authentication;
- RBAC;
- tenant scoping;
- policy enforcement;
- MCP permissions;
- guarded tool execution;
- filesystem MCP restrictions;
- PostgreSQL MCP security;
- Docker MCP security;
- input/output redaction;
- prompt-injection pattern detection;
- Human Review escalation;
- request correlation;
- security headers;
- rate-limit middleware;
- idempotency middleware;
- production configuration guards;
- Kubernetes network policies;
- secret-scanning workflow support.

See `SECURITY.md` and the repository security documentation for deployment-specific requirements and limitations.

---

## Design Principles

**Explicit orchestration** — Agent execution is represented through structured graphs and services rather than hidden inside a single prompt loop.

**Provider independence** — Agents consume the Model Gateway rather than depending directly on a specific model vendor.

**Controlled tool boundaries** — Tool and MCP execution can pass through permissions, policy, and security controls.

**Durability** — Long-running operations can persist state and resume instead of depending entirely on synchronous execution.

**Human oversight** — Selected actions can be escalated to persistent Human Review workflows.

**Observability** — Runtime behavior is exposed through metrics, tracing, structured logging, health checks, and performance monitoring.

**Tenant-aware governance** — Identity, RBAC, tenant scoping, and model controls are represented as platform concerns.

**Infrastructure as code** — Docker, Kubernetes, Helm, and Pulumi assets are maintained with the application.

---

## Current Scope

RedPA AI is an engineering and portfolio platform demonstrating how production-oriented agentic systems can be structured.

V4.2 contains implementations across orchestration, model routing, tools, MCP, A2A, workflows, memory, evaluation, policy, identity, messaging, and observability.

Some capabilities depend on external configuration or infrastructure, including provider credentials, OAuth provider configuration, GitHub access, external model endpoints, and cloud deployment.

---

## Release

**Current source release: V4.2**

V4.2 adds the production-agentic runtime layer with particular focus on:

```text
Multi-provider inference
        +
Cost-aware routing
        +
Provider fallback
        +
Runtime guardrails
        +
Evaluation gates
        +
Reliability controls
        +
AI telemetry
        +
Tenant-aware model governance
```

For detailed changes, see:

```text
CHANGELOG.md
docs/V4_2_PRODUCTION_AGENTIC_READINESS.md
```

---

## Contributing

Please read `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md` before contributing.

---

## License

RedPA AI is released under the **MIT License**.

See `LICENSE` for details.

---

<p align="center">
  <strong>RedPA AI V4.2</strong><br>
  Building agentic systems as software infrastructure — not just LLM demos.
</p>

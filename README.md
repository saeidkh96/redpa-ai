<p align="center">
  <img src="docs/images/logo.png" width="220" alt="RedPA AI">
</p>

<h1 align="center">RedPA AI</h1>

<p align="center">
  <strong>Enterprise Agentic AI Platform</strong>
</p>

<p align="center">
Production-oriented multi-agent orchestration, MCP tool execution, A2A communication, durable workflows, semantic memory, human approval, and distributed observability.
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)
![Next.js](https://img.shields.io/badge/Next.js-Control_Center-black)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791)
![Release](https://img.shields.io/badge/Release-v2.0.0-success)
![License](https://img.shields.io/badge/License-MIT-green)

</p>

------------------------------------------------------------------------

> **A production-oriented Agentic AI platform for multi-agent
> orchestration, enterprise tool execution, durable workflows, semantic
> memory, and distributed observability.**

RedPA AI is a modular backend platform for building real-world Agentic
AI systems. It combines planner-based routing, Retrieval-Augmented
Generation (RAG), Model Context Protocol (MCP), Agent-to-Agent (A2A)
communication, Human-in-the-Loop approval, durable workflow execution,
long-term Agent Memory, background jobs, and production-grade
observability in one extensible architecture.

The platform is designed as an engineering foundation rather than a
single LLM wrapper. Its architecture separates APIs, orchestration,
tools, workflows, memory, background processing, monitoring, and
deployment, allowing every subsystem to evolve independently while
remaining production-ready.

------------------------------------------------------------------------

## Table of Contents

-   [Overview](#overview)
-   [Architecture](#architecture)
-   [Key Capabilities](#key-capabilities)
-   [System Components](#system-components)
-   [Technology Stack](#technology-stack)
-   [Repository Structure](#repository-structure)
-   [Quick Start](#quick-start)
-   [Configuration](#configuration)
-   [API Overview](#api-overview)
-   [MCP Integration](#mcp-integration)
-   [A2A Multi-Agent System](#a2a-multi-agent-system)
-   [Durable Workflows](#durable-workflows)
-   [Human-in-the-Loop](#human-in-the-loop)
-   [Agent Memory](#agent-memory)
-   [Background Jobs](#background-jobs)
-   [Observability](#observability)
-   [Security](#security)
-   [Health and Performance](#health-and-performance)
-   [Deployment](#deployment)
-   [Testing and CI](#testing-and-ci)
-   [Release Status](#release-status)
-   [Roadmap](#roadmap)
-   [License](#license)

------------------------------------------------------------------------

## Overview

RedPA AI is an enterprise-oriented Agentic AI platform that enables
intelligent agents to collaborate, use external tools, execute
long-running workflows, maintain semantic memory, and safely interact
with production systems. It combines modern AI engineering practices
with backend infrastructure to build reliable, scalable, and observable
AI applications.

------------------------------------------------------------------------

## RedPA AI v2 Control Center

RedPA AI v2.0.0 adds an operator-facing web Control Center for
inspecting and operating the platform from one interface.

The Control Center includes:

-   **Agent Control Center** --- agent registry and capability discovery
-   **Durable Workflow Visualizer** --- persisted workflows, subtasks,
    execution state, and aggregated results
-   **Human Review Console** --- approve, reject, and resume
    approval-gated workflows
-   **Agent Memory Explorer** --- inspect and semantically search stored
    memories
-   **MCP & Tool Console** --- authenticated MCP registry, tool catalog,
    and safe tool execution
-   **Observability & Operations** --- dependency health, background
    runtime, metrics, and performance
-   **Security & Production Readiness** --- security controls and
    release-gate visibility
-   **V2 Release Readiness** --- platform and frontend release status

Local Control Center:

``` text
http://localhost:3001
```

The validated v2 MCP control plane currently exposes **19 tools across 4
MCP servers**: Docker, Filesystem, GitHub, and PostgreSQL.

------------------------------------------------------------------------

## Architecture

``
<p align="center">
```
`<img
    src="docs/images/architecture.png"
    alt="RedPA AI Architecture"
    width="100%"
  />
``
</p>
```

------------------------------------------------------------------------

## Key Capabilities

Modern AI applications need more than prompt execution.

A production-grade system must be able to:

-   coordinate multiple agents;
-   route requests to the correct workflow;
-   retrieve external and internal knowledge;
-   call tools safely;
-   delegate work to remote specialist agents;
-   pause for human approval;
-   persist long-running state;
-   recover after interruption;
-   maintain semantic memory;
-   process work asynchronously;
-   expose health and performance data;
-   provide logs, metrics, and distributed traces;
-   run consistently across local, Docker, and Kubernetes environments.

RedPA AI provides these capabilities as one integrated platform.

------------------------------------------------------------------------

## Key Capabilities

### Agentic AI

-   Planner-based task routing
-   Multi-agent orchestration
-   Chat workflows
-   Research workflows
-   Tool execution workflows
-   Retrieval-Augmented Generation
-   Context-aware conversations
-   Remote specialist delegation
-   Shared agent context

### Model Context Protocol

-   MCP server registry
-   Dynamic tool discovery
-   Unified tool execution
-   Filesystem MCP server
-   GitHub MCP server
-   PostgreSQL MCP server
-   Docker MCP server
-   Permission-aware tool calls
-   Approval support for risky actions

### Agent-to-Agent Communication

-   A2A Agent Cards
-   Remote agent discovery
-   Capability-based routing
-   Coordinator Agent
-   Parallel subtask execution
-   Aggregated multi-agent responses
-   Specialist status normalization
-   Distributed task delegation

### Workflow Reliability

-   Durable workflow persistence
-   Workflow checkpoints
-   Workflow resumption
-   Retry support
-   Human approval
-   Distributed subtask tracking
-   Failed and running task recovery
-   Idempotent requests

### Agent Memory

-   Long-term memory
-   Semantic memory
-   Shared agent memory
-   Memory search
-   Memory summarization
-   Memory deduplication
-   Memory retention policies
-   PostgreSQL and Qdrant-backed storage

### Platform Runtime

-   Redis distributed cache
-   Rate limiting
-   Idempotency middleware
-   Background Worker
-   Scheduler
-   Delayed jobs
-   Retry queue
-   Dead-letter queue
-   Worker and Scheduler heartbeats

### Observability

-   Prometheus metrics
-   Grafana integration
-   OpenTelemetry tracing
-   Tempo trace storage
-   Structured JSON logging
-   Request IDs
-   Correlation IDs
-   Trace IDs and Span IDs
-   Slow request detection
-   Slow SQL detection
-   Dependency health checks

### Deployment

-   Docker
-   Docker Compose
-   Kubernetes manifests
-   Helm chart
-   Readiness, liveness, and startup probes
-   Non-root container security context
-   Resource requests and limits
-   Horizontal Pod Autoscaling

------------------------------------------------------------------------

## Architecture

``` mermaid
flowchart TB
    Client[Client / API Consumer]

    subgraph API["FastAPI Platform"]
        Auth[Authentication]
        Conversations[Conversations & Messages]
        Planner[Planner / Router]
        Reviews[Human Review]
        Jobs[Background Jobs API]
        Health[Health & Performance APIs]
    end

    subgraph Agents["Agent Runtime"]
        ChatAgent[Chat Agent]
        RagAgent[RAG Agent]
        ResearchAgent[Research Agent]
        ToolAgent[Tool Agent]
        Coordinator[A2A Coordinator]
    end

    subgraph Specialists["Remote Specialist Agents"]
        ResearchSpecialist[Research Specialist]
        PostgresSpecialist[PostgreSQL Specialist]
        DockerSpecialist[Docker Specialist]
        FilesystemSpecialist[Filesystem Specialist]
        GitHubSpecialist[GitHub Specialist]
    end

    subgraph MCP["MCP Tool Layer"]
        FilesystemMCP[Filesystem MCP]
        GitHubMCP[GitHub MCP]
        PostgresMCP[PostgreSQL MCP]
        DockerMCP[Docker MCP]
    end

    subgraph Runtime["Workflow & Runtime Services"]
        Durable[Durable Workflows]
        Memory[Agent Memory]
        Worker[Background Worker]
        Scheduler[Scheduler]
        Redis[Redis]
    end

    subgraph Storage["Data Layer"]
        Postgres[(PostgreSQL)]
        Qdrant[(Qdrant)]
    end

    subgraph Observability["Observability"]
        Prometheus[Prometheus]
        Grafana[Grafana]
        Collector[OpenTelemetry Collector]
        Tempo[Tempo]
    end

    Client --> API
    Planner --> ChatAgent
    Planner --> RagAgent
    Planner --> ResearchAgent
    Planner --> ToolAgent
    Planner --> Coordinator

    Coordinator --> Specialists
    ToolAgent --> MCP
    Reviews --> Durable
    Agents --> Durable
    Durable --> Memory
    Jobs --> Worker
    Scheduler --> Worker
    Worker --> Redis

    Conversations --> Postgres
    Durable --> Postgres
    Memory --> Postgres
    Memory --> Qdrant
    RagAgent --> Qdrant
    MCP --> Postgres

    API --> Prometheus
    Agents --> Collector
    Collector --> Tempo
    Prometheus --> Grafana
    Tempo --> Grafana
```

------------------------------------------------------------------------

## System Components

### FastAPI Backend

The backend exposes the public API and coordinates the platform runtime.

Responsibilities include:

-   authentication;
-   user management;
-   conversations;
-   messages;
-   chat execution;
-   document ingestion;
-   human reviews;
-   MCP tools;
-   A2A coordination;
-   durable workflows;
-   Agent Memory;
-   background jobs;
-   health and monitoring endpoints.

### Planner and Routing

The Planner analyzes a request and selects the appropriate execution
path.

Typical routes include:

-   direct chat;
-   RAG;
-   research;
-   internal tools;
-   MCP tools;
-   Human Review;
-   distributed A2A execution.

### Specialist Agents

Specialist agents run as separate services and expose A2A-compatible
Agent Cards.

Current specialists include:

-   Research Agent
-   PostgreSQL Agent
-   Docker Agent
-   Filesystem Agent
-   GitHub Agent

### MCP Servers

Each MCP service provides a focused tool boundary.

This separation improves:

-   security;
-   testability;
-   service isolation;
-   capability discovery;
-   permission management;
-   deployment flexibility.

### Durable Workflow Engine

The durable workflow layer persists state and allows interrupted or
failed execution to continue later.

It supports:

-   workflow creation;
-   subtask persistence;
-   approval state;
-   resume logic;
-   failed-task retry;
-   running-task recovery;
-   metadata normalization;
-   final workflow aggregation.

### Agent Memory

The memory subsystem combines relational persistence and vector search.

PostgreSQL stores structured memory metadata.

Qdrant stores semantic representations for similarity-based retrieval.

------------------------------------------------------------------------

## Technology Stack

  Area                  Technologies
  --------------------- ------------------------------------
  Backend               Python, FastAPI, Pydantic
  Database              PostgreSQL, SQLAlchemy, asyncpg
  Vector Database       Qdrant
  Cache and Runtime     Redis
  Agent Orchestration   LangGraph-style stateful workflows
  LLM Runtime           Ollama
  Agent Protocols       MCP, A2A
  Containers            Docker, Docker Compose
  Metrics               Prometheus
  Dashboards            Grafana
  Tracing               OpenTelemetry, Tempo
  Testing               pytest, pytest-asyncio
  Deployment            Kubernetes, Helm
  CI                    GitHub Actions

------------------------------------------------------------------------

## Repository Structure

``` text
redpa-ai/
├── backend/
│   └── app/
│       ├── a2a_protocol/
│       ├── agent_memory/
│       ├── api/
│       │   └── v1/
│       ├── background_jobs/
│       ├── core/
│       ├── database/
│       ├── distributed_durable/
│       ├── errors/
│       ├── health/
│       ├── logging_config/
│       ├── mcp/
│       ├── mcp_servers/
│       ├── middleware/
│       ├── monitoring/
│       ├── observability/
│       ├── performance/
│       ├── research/
│       ├── runtime_cache/
│       ├── security_hardening/
│       ├── specialist_agents/
│       └── main.py
├── frontend/
├── config/
├── deploy/
│   ├── helm/
│   └── kubernetes/
├── docs/
├── observability/
├── tests/
├── .github/
│   └── workflows/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── VERIFY_V2_RELEASE.ps1
├── BUILD_V2_RELEASE.ps1
├── RELEASE_NOTES_v2.0.0.md
└── README.md
```

------------------------------------------------------------------------

## Quick Start

### Requirements

Install:

-   Python 3.13+
-   Docker Desktop
-   Docker Compose
-   Git
-   Ollama, if using a local model outside Docker

### Clone

``` bash
git clone https://github.com/<your-username>/redpa-ai.git
cd redpa-ai
```

### Create the virtual environment

Windows PowerShell:

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux or macOS:

``` bash
python -m venv .venv
source .venv/bin/activate
```

### Install dependencies

``` bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Configure environment variables

``` bash
cp .env.example .env
```

On Windows:

``` powershell
Copy-Item .env.example .env
```

Review `.env` before starting the platform.

### Validate the project

``` bash
python -m compileall backend/app
python -m pytest tests -v
docker compose config
```

### Start the platform

``` bash
docker compose up -d --build
```

### Check the services

``` bash
docker compose ps
```

### Open the platform

``` text
Control Center:  http://localhost:3001
```

### Open the API

``` text
Swagger UI:     http://localhost:8000/docs
OpenAPI:        http://localhost:8000/openapi.json
Health:         http://localhost:8000/api/v1/platform/health
Readiness:      http://localhost:8000/api/v1/platform/ready
Liveness:       http://localhost:8000/api/v1/platform/live
Metrics:        http://localhost:8000/api/v1/metrics
Performance:    http://localhost:8000/api/v1/performance/snapshot
Prometheus:     http://localhost:9090
Grafana:        http://localhost:3000
Tempo:          http://localhost:3200
Qdrant:         http://localhost:6333
```

------------------------------------------------------------------------

## Configuration

Important environment variables:

``` env
APP_NAME=RedPA AI
APP_VERSION=0.2.0
ENVIRONMENT=development
DEBUG=true

API_V1_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8000

DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333

SECRET_KEY=replace-with-a-long-secret
JWT_SECRET_KEY=replace-with-a-long-jwt-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60

OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b

OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
TEMPO_URL=http://tempo:3200
OTEL_COLLECTOR_HEALTH_URL=http://otel-collector:13133

RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW_SECONDS=60
IDEMPOTENCY_TTL_SECONDS=86400

SLOW_REQUEST_THRESHOLD_MS=1000
SLOW_QUERY_THRESHOLD_MS=500

JSON_LOGS=true
LOG_LEVEL=INFO
EXPOSE_ERROR_DETAILS=true

REQUIRE_HTTPS=false
ALLOWED_HOSTS=localhost,127.0.0.1,backend
```

For production:

``` env
ENVIRONMENT=production
DEBUG=false
JSON_LOGS=true
EXPOSE_ERROR_DETAILS=false
REQUIRE_HTTPS=true
```

Use strong secrets and restrict allowed hosts.

------------------------------------------------------------------------

## API Overview

The platform groups endpoints under `/api/v1`.

Main API areas include:

  Area                    Purpose
  ----------------------- ------------------------------------
  `/auth`                 Authentication and token handling
  `/users`                User management
  `/conversations`        Conversation lifecycle
  `/messages`             Conversation messages
  `/chat`                 Agentic chat execution
  `/documents`            Document ingestion and retrieval
  `/reviews`              Human Review workflows
  `/tools`                Internal tools
  `/mcp`                  MCP operations
  `/unified-tools`        Unified tool catalog and execution
  `/agents`               Agent management
  `/remote-agents`        Remote A2A agents
  `/multi-agents`         Multi-agent execution
  `/distributed-agents`   Distributed specialist execution
  `/durable-workflows`    Durable workflow API
  `/agent-memory`         Memory operations
  `/jobs`                 Background jobs
  `/platform`             Health endpoints
  `/performance`          Runtime performance
  `/metrics`              Prometheus metrics

The exact request and response schemas are available in Swagger UI.

------------------------------------------------------------------------

## MCP Integration

RedPA AI implements MCP as a tool platform rather than embedding every
integration directly into the backend.

### MCP Services

``` text
Filesystem MCP   : 8010
GitHub MCP       : 8020
PostgreSQL MCP   : 8030
Docker MCP       : 8040
```

### MCP Capabilities

-   server registration;
-   dynamic discovery;
-   tool metadata;
-   argument validation;
-   permission checks;
-   safe execution;
-   unified qualified names;
-   response formatting;
-   private network validation.

### Security Examples

The Filesystem MCP:

-   blocks path traversal;
-   blocks sensitive environment files;
-   restricts access to the configured sandbox.

The PostgreSQL MCP:

-   permits read-only queries;
-   blocks write operations;
-   blocks multi-statement SQL;
-   blocks unsafe PostgreSQL functions;
-   blocks comments and locking clauses.

The Docker MCP:

-   validates container names;
-   limits log output;
-   rejects unsafe resource references;
-   uses read-only Docker socket access where configured.

------------------------------------------------------------------------

## A2A Multi-Agent System

RedPA AI supports distributed Agent-to-Agent execution.

### Coordinator Responsibilities

The coordinator:

1.  parses a complex request;
2.  creates subtasks;
3.  discovers suitable agents;
4.  selects capabilities;
5.  delegates work;
6.  runs independent tasks in parallel;
7.  aggregates results;
8.  reports failed and successful subtasks.

### Specialist Services

``` text
A2A Coordinator      : 8050
Research Agent       : 8061
PostgreSQL Agent     : 8062
Docker Agent         : 8063
Filesystem Agent     : 8064
GitHub Agent         : 8065
```

### Agent Cards

Each remote service exposes an Agent Card under:

``` text
/.well-known/agent-card.json
```

The card describes:

-   agent identity;
-   protocol version;
-   capabilities;
-   available skills;
-   endpoint information.

------------------------------------------------------------------------

## Durable Workflows

Durable workflows are designed for tasks that cannot be treated as one
synchronous request.

Examples include:

-   distributed research;
-   approval-gated tool execution;
-   multi-step data workflows;
-   tasks that must survive service restart;
-   workflows with retryable subtasks.

### Workflow Lifecycle

``` text
Create
  |
Persist
  |
Execute subtasks
  |
Pause for approval or failure
  |
Resume
  |
Aggregate
  |
Finalize
```

The platform stores:

-   workflow status;
-   original request;
-   metadata;
-   subtask states;
-   remote agent identifiers;
-   results;
-   errors;
-   execution timing;
-   retry state.

------------------------------------------------------------------------

## Human-in-the-Loop

Risky operations can be paused before execution.

Typical approval cases include:

-   sending email;
-   modifying external systems;
-   executing high-risk tools;
-   performing actions with irreversible effects.

The Human Review flow supports:

-   review creation;
-   pending review listing;
-   approval;
-   rejection;
-   edited responses;
-   workflow resumption;
-   prevention of duplicate review creation after approval.

------------------------------------------------------------------------

## Agent Memory

The Agent Memory layer enables agents to reuse relevant information
across workflows.

### Memory Types

-   private agent memory;
-   shared memory;
-   semantic memory;
-   long-term structured memory;
-   summarized memory.

### Memory Operations

-   create;
-   retrieve;
-   search;
-   inject into context;
-   summarize;
-   deduplicate;
-   retain;
-   analyze.

### Storage

PostgreSQL stores structured records and metadata.

Qdrant supports semantic similarity search.

------------------------------------------------------------------------

## Background Jobs

The background runtime is backed by PostgreSQL and Redis.

### Capabilities

-   delayed execution;
-   retry with exponential backoff;
-   maximum-attempt control;
-   dead-letter queue;
-   concurrent Worker execution;
-   Scheduler;
-   job status API;
-   Worker heartbeat;
-   Scheduler heartbeat.

### Job States

``` text
queued
running
completed
dead_letter
```

### Example Job

``` json
{
  "job_type": "sleep",
  "payload": {
    "seconds": 2
  },
  "max_attempts": 3,
  "delay_seconds": 0
}
```

------------------------------------------------------------------------

## Observability

RedPA AI includes metrics, logs, traces, and health monitoring.

### Prometheus

Prometheus scrapes:

``` text
GET /api/v1/metrics
```

Examples of custom metrics:

``` text
redpa_slow_requests_total
redpa_request_duration_seconds
redpa_slow_sql_queries_total
redpa_sql_query_duration_seconds
```

### OpenTelemetry

Instrumentation includes:

-   FastAPI;
-   HTTPX;
-   Redis;
-   asyncpg;
-   logging.

### Tempo

Tempo stores distributed traces received through the OpenTelemetry
Collector.

OTLP ports:

``` text
4317 gRPC
4318 HTTP
```

Tempo readiness:

``` text
GET http://localhost:3200/ready
```

### Structured Logging

JSON logs can include:

-   timestamp;
-   level;
-   logger;
-   message;
-   request ID;
-   correlation ID;
-   trace ID;
-   span ID;
-   path;
-   method;
-   status;
-   execution time;
-   workflow ID;
-   job ID;
-   error code;
-   error ID.

------------------------------------------------------------------------

## Security

Security features include:

-   JWT authentication;
-   security response headers;
-   CORS configuration;
-   API-key hashing foundation;
-   rate limiting;
-   idempotency conflict detection;
-   environment validation;
-   production secret validation;
-   optional HTTPS enforcement;
-   allowed-host validation;
-   safe MCP input validation;
-   read-only tool policies;
-   Kubernetes non-root execution;
-   dropped Linux capabilities;
-   read-only root filesystem support.

### Idempotency

For supported write requests, send:

``` text
Idempotency-Key: unique-request-key
```

Repeated identical requests return the stored response.

Reusing the same key with a different request produces a conflict
response.

### Rate Limiting

Default settings:

``` env
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW_SECONDS=60
```

Rate-limit response headers include:

``` text
X-RateLimit-Limit
X-RateLimit-Remaining
```

------------------------------------------------------------------------

## Health and Performance

### Liveness

``` text
GET /api/v1/platform/live
```

Confirms that the backend process is running.

### Readiness

``` text
GET /api/v1/platform/ready
```

Checks critical dependencies.

### Deep Health

``` text
GET /api/v1/platform/health
```

Checks:

-   PostgreSQL;
-   Redis;
-   Qdrant;
-   Tempo;
-   OpenTelemetry Collector;
-   Background Worker;
-   Background Scheduler.

### Performance Snapshot

``` text
GET /api/v1/performance/snapshot
```

Provides:

-   slow request threshold;
-   slow query threshold;
-   queued jobs;
-   running jobs;
-   dead-letter jobs.

### Performance Headers

Responses can include:

``` text
X-Request-ID
X-Correlation-ID
X-Process-Time-Ms
X-Performance-Time-Ms
X-Trace-ID
X-Span-ID
```

------------------------------------------------------------------------

## Deployment

### Docker Compose

Validate:

``` bash
docker compose config
```

Start:

``` bash
docker compose up -d --build
```

Stop:

``` bash
docker compose down
```

Remove volumes:

``` bash
docker compose down -v
```

### Kubernetes

Resources are located under:

``` text
deploy/kubernetes
deploy/helm/redpa
```

### Helm

Validate:

``` bash
helm lint deploy/helm/redpa
```

Install:

``` bash
helm upgrade --install redpa deploy/helm/redpa \
  --namespace redpa \
  --create-namespace \
  --set secretEnv.DATABASE_URL="..." \
  --set secretEnv.SECRET_KEY="..." \
  --set secretEnv.API_KEY_PEPPER="..."
```

The chart includes:

-   Deployment;
-   Service;
-   Secret;
-   Ingress;
-   Horizontal Pod Autoscaler;
-   health probes;
-   resource limits;
-   security context.

------------------------------------------------------------------------

## Testing and CI

Compile the backend:

``` bash
python -m compileall backend/app
```

Validate Docker Compose:

``` bash
docker compose config
```

When pytest tests are present, run:

``` bash
python -m pytest tests -v
```

> **v2.0.0 validation note:** the final release verification found no
> active pytest tests to execute. The v2 release therefore does not
> claim that a unit-test suite passed.

The v2 release gate was validated through automated and manual
integration checks covering:

-   Python source compilation;
-   Docker Compose configuration;
-   liveness and readiness;
-   deep platform health;
-   performance snapshot;
-   Prometheus metrics;
-   Control Center availability;
-   JWT authentication;
-   MCP authentication boundaries;
-   authenticated MCP control plane;
-   frontend production build;
-   agent capability discovery;
-   durable workflow visualization;
-   Human Review approval and workflow resume;
-   Agent Memory semantic search;
-   MCP registry and tool discovery;
-   end-to-end execution of a safe MCP tool.

Windows release verification:

``` powershell
powershell -ExecutionPolicy Bypass -File .\VERIFY_V2_RELEASE.ps1
```

### GitHub Actions

CI is used for dependency installation, compilation, application import,
test execution when tests are present, and project validation.

------------------------------------------------------------------------

## Release Status

### v2.0.0

**Status: Released**

v2.0.0 includes:

-   operator-facing Control Center;
-   distributed agent discovery and orchestration;
-   durable workflows;
-   Human-in-the-Loop workflow control;
-   semantic Agent Memory;
-   authenticated MCP control plane;
-   4 MCP servers and 19 tools;
-   production observability;
-   security and release-readiness checks.

Release notes:

``` text
RELEASE_NOTES_v2.0.0.md
```

Release artifact:

``` text
redpa-ai-v2.0.0.zip
```

SHA256:

``` text
B1AD542FF99B82CD0F55C5305D848F41F4E589BAFC5DBFCA902F46FEE208224C
```

------------------------------------------------------------------------

## Roadmap

### Completed

-   [x] Authentication
-   [x] Conversations and Messages
-   [x] Planner and Routing
-   [x] RAG
-   [x] MCP
-   [x] Unified Tool Registry
-   [x] Human Review
-   [x] Workflow Resume
-   [x] A2A Coordinator
-   [x] Specialist Agents
-   [x] Distributed Durable Workflows
-   [x] Agent Memory
-   [x] Redis Cache
-   [x] Rate Limiting
-   [x] Idempotency
-   [x] Background Worker
-   [x] Scheduler
-   [x] Retry Queue
-   [x] Dead-Letter Queue
-   [x] Prometheus
-   [x] Grafana
-   [x] OpenTelemetry
-   [x] Tempo
-   [x] Structured Logging
-   [x] Global Error Framework
-   [x] Health and Performance APIs
-   [x] Docker Compose
-   [x] Kubernetes
-   [x] Helm
-   [x] CI

### Future Work

-   [x] Web Control Center
-   [ ] Multi-tenancy
-   [ ] Role-based access control
-   [ ] OAuth providers
-   [ ] Cloud deployment reference architecture
-   [ ] Advanced policy engine
-   [ ] Agent evaluation dashboard
-   [ ] Cost and token analytics
-   [ ] Model provider abstraction
-   [ ] Event-driven external integrations
-   [ ] Expanded automated test coverage

------------------------------------------------------------------------

## Engineering Highlights

RedPA AI demonstrates practical experience with:

-   Agentic AI system design;
-   multi-agent orchestration;
-   distributed services;
-   RAG;
-   MCP;
-   A2A;
-   stateful workflow execution;
-   Human-in-the-Loop systems;
-   semantic memory;
-   asynchronous job processing;
-   API security;
-   observability;
-   containerization;
-   Kubernetes deployment;
-   CI and release engineering.

------------------------------------------------------------------------

## License

This project is licensed under the MIT License.

Copyright (c) 2026 Saeid Khalilian

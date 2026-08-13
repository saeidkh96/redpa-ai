# RedPA AI V6.0 Architecture

## Scope

This document describes the architecture represented by the V6.0 repository. Reference deployment assets are labeled separately from runtime implementation.

## Developer Layer

```text
Python Applications                         Operators / CI
       |                                         |
       +---- RedPA Python SDK (sync/async)        +---- redpa CLI
                         \                         /
                          \                       /
                           +---- HTTP /api/v1 ---+
                                      |
                                      v
```

## Runtime Architecture

```text
                         +---------------------------+
                         |      Next.js Control      |
                         |           Plane           |
                         +-------------+-------------+
                                       |
                                       v
+------------------+       +-----------+-----------+       +------------------+
| Python SDK / CLI | ----> |     FastAPI API       | <---- | External Clients |
+------------------+       | Auth / Tenancy / API  |       +------------------+
                           +-----------+-----------+
                                       |
             +-------------------------+-------------------------+
             |                         |                         |
             v                         v                         v
    +--------+--------+       +--------+--------+       +--------+--------+
    | Agent Runtime   |       | Model Gateway   |       | Governance /    |
    | Planner / RAG   |       | Providers       |       | Policy / HITL   |
    | Research / Tool |       | Reliability     |       | Reviews         |
    +--------+--------+       +--------+--------+       +--------+--------+
             |                         |                         |
             +-------------+-----------+-------------------------+
                           |
             +-------------+---------------------------+
             |                         |               |
             v                         v               v
    +--------+--------+       +--------+--------+  +---+----------------+
    | Durable         |       | MCP Tool Layer  |  | A2A / Specialist  |
    | Workflows       |       | + MCP Servers   |  | Agent Services    |
    +--------+--------+       +--------+--------+  +---+----------------+
             |                         |               |
             +-------------------------+---------------+
                                       |
                                       v
                           +-----------+-----------+
                           | Persistence / Runtime |
                           | PostgreSQL            |
                           | Qdrant                |
                           | Redis                 |
                           +-----------+-----------+
                                       |
                                       v
                           +-----------+-----------+
                           | Observability         |
                           | Prometheus / Grafana  |
                           | OpenTelemetry / Tempo |
                           +-----------------------+
```

## Implemented Repository Boundaries

### API and identity
FastAPI exposes the V1 API surface. Authentication, tenant-aware access, API middleware, error handling, and health surfaces are implemented server-side.

### Agent runtime
The repository contains planner, RAG/retrieval, research, tool, specialist-agent, distributed-agent, and human-review capabilities. Agent registry/discovery is exposed through the API.

### Durable execution
Distributed durable workflows persist execution state and support retrieval and resume operations. Background-job and runtime-cache packages provide supporting execution infrastructure.

### Tool interoperability
MCP server discovery, health, tool cataloging, and qualified tool execution are exposed through implemented API routes. A2A packages and specialist-agent services provide agent-to-agent integration surfaces.

### Model and quality plane
The model gateway contains provider integration, economics/reliability functionality, and related governance. Evaluation APIs include benchmark and release-quality capabilities.

### Data
PostgreSQL-backed models/repositories provide transactional persistence. Qdrant-backed vector/retrieval services support semantic retrieval. Redis-backed runtime components support cache/background coordination.

### Observability
The repository contains metrics/tracing instrumentation and Docker services for Prometheus, Grafana, OpenTelemetry/Tempo-oriented observability.

### Developer platform
V6.0 adds the installable Python SDK, asynchronous SDK client, `redpa` CLI, examples, package build metadata, and dedicated SDK CI.

## Deployment Assets

Docker Compose is the primary local multi-service runtime represented in the repository. Kubernetes/Helm and Azure/Pulumi assets are deployment/reference architecture surfaces and should not be interpreted as proof of a live hosted production deployment.

## V6.0 Version Contract

The release metadata for the V6 source tree is aligned to `6.0.0` across:

- backend default application version;
- Docker Compose backend application version;
- frontend package metadata;
- Python SDK package metadata.

Runtime overrides can still replace configured application version through environment variables.

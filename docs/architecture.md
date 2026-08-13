# RedPA AI Architecture

## Overview

RedPA AI is a production-oriented Agentic AI platform built around FastAPI,
LangGraph-style orchestration, PostgreSQL, Qdrant, Redis, MCP, A2A specialist
agents, background jobs, human approval, durable workflows, and distributed
observability.

## High-Level Flow

```text
Client
  |
  v
FastAPI API Gateway
  |
  +--> Authentication and Users
  |
  +--> Conversations and Messages
  |
  +--> Planner / Router
  |      |
  |      +--> Chat Agent
  |      +--> RAG Agent
  |      +--> Research Agent
  |      +--> Tool Agent
  |      +--> Human Review
  |
  +--> MCP Tool Layer
  |      |
  |      +--> Filesystem MCP
  |      +--> GitHub MCP
  |      +--> PostgreSQL MCP
  |      +--> Docker MCP
  |
  +--> A2A Coordinator
  |      |
  |      +--> Research Specialist
  |      +--> PostgreSQL Specialist
  |      +--> Docker Specialist
  |      +--> Filesystem Specialist
  |      +--> GitHub Specialist
  |
  +--> Durable Distributed Workflows
  |
  +--> Agent Memory
  |      |
  |      +--> PostgreSQL Long-Term Memory
  |      +--> Qdrant Semantic Memory
  |      +--> Shared Agent Memory
  |
  +--> Background Runtime
         |
         +--> Redis
         +--> Worker
         +--> Scheduler
         +--> Retry Queue
         +--> Dead-Letter Queue
```

## Data Stores

### PostgreSQL

Used for:

- users;
- conversations;
- messages;
- reviews;
- durable workflows;
- workflow subtasks;
- background jobs;
- long-term Agent Memory.

### Qdrant

Used for:

- document embeddings;
- RAG retrieval;
- semantic Agent Memory search.

### Redis

Used for:

- distributed cache;
- rate limiting;
- idempotency responses;
- Worker and Scheduler heartbeats.

## Observability

```text
Backend and Agents
      |
      +--> Prometheus Metrics
      |
      +--> OpenTelemetry Traces
                |
                v
       OpenTelemetry Collector
                |
                v
              Tempo
```

Grafana can use Prometheus for metrics and Tempo for distributed traces.

## Reliability

The platform includes:

- durable workflow persistence;
- workflow resumption;
- human approval;
- idempotent request handling;
- background retries;
- dead-letter jobs;
- readiness and liveness endpoints;
- dependency health checks;
- slow-request detection;
- slow-query detection.

## Security

The platform includes:

- JWT authentication;
- CORS configuration;
- API-key hashing foundation;
- security response headers;
- production environment validation;
- rate limiting;
- idempotency conflict detection;
- Kubernetes non-root security context;
- Secret resources and HTTPS-ready ingress.

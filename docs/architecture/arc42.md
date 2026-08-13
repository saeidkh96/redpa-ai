# RedPA AI — arc42 Architecture Documentation

## 1. Introduction and Goals

RedPA AI is an enterprise-oriented agentic AI platform that coordinates
models, agents, tools, workflows, retrieval, policy enforcement, human review,
memory, and observability.

Primary quality goals:

1. Safety
2. Reliability
3. Auditability
4. Extensibility
5. Observability
6. Testability

## 2. Constraints

- Python / FastAPI remains the primary backend platform.
- Java / Spring Boot is used for the policy microservice.
- PostgreSQL is the primary relational store.
- Qdrant is used for vector retrieval.
- Redis supports runtime coordination.
- Docker Compose remains the local integration environment.
- Existing working capabilities must not be broken by architecture refactoring.

## 3. Context and Scope

External actors and systems:

- end users and operators;
- model providers;
- MCP servers;
- GitHub / external APIs;
- infrastructure services.

See `c4.md` for context diagrams.

## 4. Solution Strategy

RedPA uses:

- bounded contexts;
- service-oriented modularization;
- async-first APIs;
- adapter-based integrations;
- durable workflows;
- policy gates;
- Human-in-the-Loop controls;
- observability and audit trails.

## 5. Building Block View

Main building blocks:

- Platform API
- Agent Runtime
- Model Gateway
- RAG / Knowledge
- Tool / MCP Runtime
- Human Review
- Policy Engine
- Agent Memory
- Background Runtime
- Observability

## 6. Runtime View

### Tool execution

```text
User Request
  -> Planner
  -> Policy Enforcement
  -> ALLOW / REVIEW / DENY
  -> Tool / MCP execution
  -> Persist result + audit + metrics
```

### Model execution

```text
Agent
  -> Model Gateway
  -> Routing Strategy
  -> Provider
  -> Retry / Timeout / Circuit Breaker
  -> Normalized Response
```

### Human Review

```text
Risky Action
  -> Human Review
  -> Approve / Reject
  -> Resume / Stop
```

## 7. Deployment View

Local deployment uses Docker Compose with PostgreSQL, Qdrant, Redis,
FastAPI, frontend, policy service, MCP services, and observability components.

Kubernetes / Helm remain the production-oriented deployment path.

## 8. Cross-Cutting Concepts

- JWT authentication
- structured errors
- correlation IDs
- policy decisions
- audit logging
- Prometheus metrics
- distributed traces
- retries and circuit breakers
- idempotency
- schema validation

## 9. Architecture Decisions

See `docs/architecture/adr/`.

## 10. Quality Requirements

Architecture must support:

- policy enforcement before external side effects;
- resumable workflows;
- replaceable model providers;
- authenticated operational APIs;
- observable execution;
- deterministic testing of high-risk decisions.

## 11. Risks and Technical Debt

- Python modules still contain legacy layering.
- Policy enforcement must progressively cover every execution boundary.
- Multi-tenancy and RBAC remain future work.
- Cloud-specific infrastructure remains future work.
- Cross-service contracts need versioning as the platform grows.

## 12. Glossary

**A2A** — Agent-to-Agent communication.

**MCP** — Model Context Protocol.

**HITL** — Human-in-the-Loop.

**Bounded Context** — Explicit domain boundary with its own model and language.

**Policy Decision** — ALLOW, REVIEW, or DENY result produced by governance
rules.

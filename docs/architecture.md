# Architecture

RedPA AI separates API, orchestration, services, persistence, retrieval, tools, AI providers, and observability.

## Main Layers

### API Layer

Handles:

- authentication;
- users;
- conversations;
- messages;
- chat;
- documents;
- human reviews;
- tool discovery;
- metrics.

### Agent Runtime

Contains:

- explicit `AgentState`;
- planner;
- conditional routing;
- LangGraph nodes;
- response validation;
- workflow resume.

### Service Layer

Coordinates:

- chat;
- LLM access;
- planning;
- retrieval;
- documents;
- tools;
- human review;
- persistence.

### Data Layer

- PostgreSQL for relational application state;
- Qdrant for vectors;
- local storage for uploaded documents.

### AI Layer

Ollama provides chat inference and embeddings.

### Observability

Prometheus collects metrics and Grafana presents dashboards.

## Request Lifecycle

```text
HTTP Request
  ↓
Authentication
  ↓
Conversation Validation
  ↓
Message Persistence
  ↓
LangGraph Initial State
  ↓
Planner
  ↓
Conditional Route
  ↓
Capability Node
  ↓
Response Validation
  ↓
Assistant Message Persistence
  ↓
HTTP Response
```

## Design Principles

- explicit workflow state;
- deterministic routing where possible;
- structured planner output;
- safe tools;
- human approval for sensitive actions;
- user-scoped data;
- observable execution;
- extensible services and registries.

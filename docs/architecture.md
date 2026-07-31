# Architecture

RedPA AI separates API, agent orchestration, application services, persistence, retrieval, tools, AI providers, and observability.

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
- structured planner output;
- deterministic routing where possible;
- safe tools;
- human approval for sensitive actions;
- user-scoped data;
- observable execution;
- extensible services and registries.

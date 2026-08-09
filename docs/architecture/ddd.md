# Domain-Driven Design

## Strategic Design

RedPA is split into bounded contexts that reflect business and runtime
responsibilities rather than technical folders.

### Agent Orchestration

Responsibilities:

- planning;
- routing;
- agent coordination;
- workflow execution;
- durable execution state.

Core concepts:

- Agent
- Route
- Workflow
- Task
- Execution State

### Knowledge & Retrieval

Responsibilities:

- document ingestion;
- chunking;
- embeddings;
- semantic retrieval;
- grounded context.

Core concepts:

- Document
- Chunk
- Embedding
- Retrieval Query
- Context

### Human Oversight

Responsibilities:

- human review;
- approval;
- rejection;
- workflow resume.

Core concepts:

- Review
- Review Decision
- Approval Gate
- Reviewer

### Tooling & Integration

Responsibilities:

- internal tools;
- MCP servers;
- MCP tools;
- external capability execution.

Core concepts:

- Tool
- Tool Descriptor
- Tool Invocation
- Tool Result
- MCP Server

### Model Runtime

Responsibilities:

- provider abstraction;
- routing;
- fallback;
- retry;
- circuit breaker;
- token usage.

Core concepts:

- Model Provider
- Model Route
- Inference Request
- Inference Result

### Policy & Governance

Responsibilities:

- policy evaluation;
- guardrails;
- ALLOW / REVIEW / DENY;
- audit;
- enforcement.

Core concepts:

- Policy
- Rule
- Risk
- Decision
- Enforcement Event

### Platform Operations

Responsibilities:

- authentication;
- rate limiting;
- idempotency;
- background jobs;
- observability;
- health and performance.

Core concepts:

- User
- Access Token
- Job
- Metric
- Trace
- Health State

## Context Relationships

```text
Client
  |
  v
Platform Operations
  |
  +--> Agent Orchestration
  |       |
  |       +--> Knowledge & Retrieval
  |       +--> Model Runtime
  |       +--> Tooling & Integration
  |       +--> Human Oversight
  |
  +--> Policy & Governance
          |
          +--> Human Oversight
          +--> Tooling & Integration
```

## Tactical DDD Guidance

Use domain objects for business decisions and state transitions.

Prefer:

```text
domain/
application/
infrastructure/
api/
```

when a bounded context becomes large enough to justify the split.

Do not force every existing module into a new folder only for appearance.
Phase 14 documents and tests dependency direction first; migration can remain
incremental.

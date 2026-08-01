# Tool System

## Components

- `BaseTool`
- `ToolMetadata`
- `ToolExecutionResult`
- `ToolRegistry`
- `ToolService`
- Tool node
- deterministic intent detection
- response formatters
- Prometheus metrics
- external HTTP client

## Current Tools

### Calculator

Safe AST-based arithmetic without `eval`.

### DateTime

IANA time-zone-aware date and time.

### Weather

Current weather through Open-Meteo.

### Currency

Currency conversion through Frankfurter.

### GitHub

Public repository metadata.

### News

Top Hacker News stories.

### Web Search

Brave Search integration.

## Execution Flow

```text
Planner
  → route=tool
  → Tool Node
  → Tool Registry
  → Tool Service
  → Tool
  → Response Formatter
  → Persisted Assistant Message
```

## External HTTP Controls

- HTTPS-only requests;
- host allowlists;
- private-network blocking;
- retry;
- timeout;
- response-size limits;
- JSON validation;
- optional API authentication;
- metrics.

## Adding a Tool

1. Create a class under `backend/app/tools/`.
2. Inherit from `BaseTool`.
3. Implement metadata.
4. Implement `execute`.
5. Register it.
6. Add deterministic intent detection when appropriate.
7. Add a formatter.
8. Add tests.

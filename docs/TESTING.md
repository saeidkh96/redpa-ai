# Testing

## Overview

RedPA uses `pytest` for unit and integration-oriented validation.

The test suite covers:

- planner routing;
- deterministic route priority;
- internal tools;
- MCP discovery and execution;
- Filesystem sandbox security;
- PostgreSQL read-only validation;
- Docker argument validation;
- GitHub parsing and formatting;
- A2A Agent Cards;
- Remote Agent Registry;
- Remote delegation;
- automatic Agent Selection;
- Multi-Agent subtask generation;
- approval policy;
- research ranking;
- unified tool behavior.

## Run All Tests

```bash
python -m pytest tests -v
```

## Run a Specific File

```bash
python -m pytest tests/test_a2a_automatic_selection.py -v
```

## Run Matching Tests

```bash
python -m pytest tests -k "a2a or mcp" -v
```

## Compile Validation

```bash
python -m compileall backend/app
```

## Docker Validation

```bash
docker compose config
docker compose ps
```

## Service Health

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8050/health
curl http://localhost:8050/.well-known/agent-card.json
```

## A2A Manual Test

Register a Remote Agent:

```json
{
  "name": "redpa-coordinator",
  "base_url": "http://a2a-coordinator:8050",
  "enabled": true,
  "timeout_seconds": 30
}
```

Delegate:

```json
{
  "message": "Show available agents and health",
  "timeout_seconds": 60
}
```

Expected:

```text
success: true
event_count: at least 1
task_id: present
context_id: present
error: null
```

## Multi-Agent Manual Test

```json
{
  "request": "Research and infrastructure inspection",
  "subtasks": [
    {
      "id": "research",
      "instruction": "Find an agent for web research and evidence"
    },
    {
      "id": "docker",
      "instruction": "Which agent can inspect Docker containers?"
    }
  ],
  "max_parallelism": 2,
  "timeout_seconds": 90,
  "approval_granted": false
}
```

Expected:

```text
successful_subtasks: 2
failed_subtasks: 0
approval_required: false
```

## Approval Gate Test

```json
{
  "request": "Send an email to the project manager",
  "subtasks": [],
  "max_parallelism": 2,
  "timeout_seconds": 90,
  "approval_granted": false
}
```

Expected:

```text
success: false
approval_required: true
results: []
```

## Regression Expectations

A request asking which Agent owns a capability should route to A2A:

```text
Which agent can inspect Docker containers?
```

A direct operational request should route to MCP:

```text
Inspect Docker container redpa-postgres
```

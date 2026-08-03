# A2A Platform

## Purpose

RedPA uses the Google Agent-to-Agent protocol for Agent discovery, remote delegation, and distributed workflow coordination.

## Components

- Internal Agent Registry
- Typed Agent Cards
- Public A2A Coordinator
- Remote Agent Registry
- Remote Agent Card resolver
- Capability-based Agent Selection
- Multi-Agent Workflow Service
- Human Approval Gate
- A2A Prometheus metrics

## Service Endpoints

```text
GET  http://localhost:8050/health
GET  http://localhost:8050/.well-known/agent-card.json
POST http://localhost:8050/
```

## Backend API

```text
GET    /api/v1/agents
GET    /api/v1/agents/health
GET    /api/v1/agents/discover
GET    /api/v1/agents/{agent_id}
POST   /api/v1/agents/remotes
GET    /api/v1/agents/remotes
GET    /api/v1/agents/remotes/{name}/card
POST   /api/v1/agents/remotes/{name}/delegate
DELETE /api/v1/agents/remotes/{name}
POST   /api/v1/agents/multi/delegate
```

## Metrics

```text
redpa_a2a_multi_requests_total
redpa_a2a_multi_subtasks_total
redpa_a2a_multi_duration_seconds
redpa_a2a_multi_subtask_duration_seconds
redpa_a2a_approval_required_total
```

## Current Limitation

The current Coordinator mainly discovers the appropriate RedPA capability. Independent specialist Remote Agent services are planned.

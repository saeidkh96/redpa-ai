# Monitoring

## Prometheus

RedPA exports metrics for:

- HTTP requests;
- response status;
- HTTP latency;
- internal-tool execution;
- MCP execution;
- planner behavior;
- research workflows;
- A2A workflows;
- Multi-Agent execution;
- approval-gate decisions.

## A2A Metrics

```text
redpa_a2a_multi_requests_total
redpa_a2a_multi_subtasks_total
redpa_a2a_multi_duration_seconds
redpa_a2a_multi_subtask_duration_seconds
redpa_a2a_approval_required_total
```

### Multi-Agent Requests

`redpa_a2a_multi_requests_total` uses a status label such as:

```text
success
partial
failed
timeout
approval_required
```

### Multi-Agent Subtasks

`redpa_a2a_multi_subtasks_total` records:

- subtask success or failure;
- selected Remote Agent.

### Duration

Histograms record:

- complete Multi-Agent workflow duration;
- per-Agent subtask duration.

### Approval Decisions

`redpa_a2a_approval_required_total` counts requests stopped by policy before delegation.

## Service Endpoints

Prometheus:

```text
http://localhost:9090
```

Grafana:

```text
http://localhost:3000
```

Backend metrics:

```text
http://localhost:8000/metrics
```

A2A health:

```text
http://localhost:8050/health
```

## Grafana

Recommended dashboards include:

- request rate and latency;
- planner route distribution;
- tool and MCP error rate;
- MCP server availability;
- Remote Agent availability;
- A2A task latency;
- Multi-Agent success and partial-failure rate;
- approval-required count;
- research duration;
- LLM duration;
- RAG retrieval latency;
- database latency.

## Recommended Alerts

- A2A Coordinator unavailable;
- Remote Agent connection failures;
- Multi-Agent timeout increase;
- MCP server unavailable;
- tool error-rate increase;
- approval queue growth;
- PostgreSQL connectivity failures;
- Qdrant connectivity failures.

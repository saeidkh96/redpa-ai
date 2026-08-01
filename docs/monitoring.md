# Monitoring

## Stack

- application metrics endpoint;
- Prometheus;
- Grafana;
- provisioned dashboards.

## Access

```text
Prometheus: http://localhost:9090
Grafana:    http://localhost:3000
```

Development credentials:

```text
admin / admin
```

Change them outside local development.

## HTTP Metrics

- `redpa_http_requests_total`
- `redpa_http_request_duration_seconds`
- `redpa_http_requests_in_progress`
- `redpa_http_exceptions_total`
- `redpa_http_response_size_bytes`

## Tool Metrics

- `redpa_tool_executions_total`
- `redpa_tool_errors_total`
- `redpa_tool_execution_duration_seconds`

## Recommended AI and Workflow Metrics

- LLM request count;
- model latency;
- generation failures;
- planner route distribution;
- RAG retrieval latency;
- workflow starts and completions;
- paused workflows;
- pending review count;
- approval and rejection count.

## Logging

Logs should include:

- timestamp;
- level;
- request ID;
- route and method;
- workflow or conversation ID;
- duration;
- normalized exception category.

Never log passwords, tokens, secrets, authorization headers, or document contents.

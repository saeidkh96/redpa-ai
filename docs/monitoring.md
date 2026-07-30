# Monitoring

## Stack

- Application metrics endpoint
- Prometheus scraping
- Grafana data-source provisioning
- Provisioned RedPA API overview dashboard

## Access

```text
Prometheus: http://localhost:9090
Grafana:    http://localhost:3000
```

Current development credentials:

```text
admin / admin
```

Change them outside local development.

## Recommended Metrics

### HTTP

- request count by method, route, and status;
- request duration histogram;
- requests in progress;
- validation and server errors.

### AI

- LLM request count;
- model latency;
- generation failures;
- prompt and completion token estimates where available;
- planner route distribution;
- RAG retrieval latency;
- empty retrieval count.

### Workflows

- workflow starts and completions;
- failed and paused workflows;
- human-review queue size;
- approval, rejection, and retry counts;
- workflow resume latency.

### Infrastructure

- database connectivity;
- Qdrant connectivity;
- Ollama availability;
- process memory and CPU;
- container restart count.

## Logging

Logs should include:

- timestamp;
- level;
- request ID;
- authenticated user identifier when appropriate;
- route and method;
- workflow or conversation identifier;
- duration;
- normalized exception category.

Never log passwords, tokens, JWT secrets, full authorization headers, or sensitive document contents.

## Alert Ideas

- elevated 5xx rate;
- Ollama unavailable;
- Qdrant unavailable;
- PostgreSQL unavailable;
- p95 latency above threshold;
- growing pending-review queue;
- repeated workflow failures.

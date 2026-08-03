# Deployment

## Local Docker Compose

```bash
docker compose up -d --build
```

## Services

Typical services include:

- backend;
- PostgreSQL;
- Qdrant;
- Filesystem MCP;
- GitHub MCP;
- PostgreSQL MCP;
- Docker MCP;
- A2A Coordinator;
- Prometheus;
- Grafana.

## Published Ports

```text
8000  FastAPI backend
8050  A2A Coordinator
8010  Filesystem MCP
8020  GitHub MCP
8030  PostgreSQL MCP
8040  Docker MCP
5432  PostgreSQL
6333  Qdrant HTTP
6334  Qdrant gRPC
9090  Prometheus
3000  Grafana
```

## Validation

```bash
docker compose config
docker compose ps
```

## Logs

```bash
docker compose logs --tail=150 backend
docker compose logs --tail=150 a2a-coordinator
docker compose logs --tail=150 filesystem-mcp
docker compose logs --tail=150 github-mcp
docker compose logs --tail=150 postgres-mcp
docker compose logs --tail=150 docker-mcp
```

## Health

Application:

```text
http://localhost:8000/api/v1/health
```

MCP:

```text
http://localhost:8000/api/v1/mcp/health
```

A2A Coordinator:

```text
http://localhost:8050/health
```

Agent Card:

```text
http://localhost:8050/.well-known/agent-card.json
```

Prometheus:

```text
http://localhost:9090
```

Grafana:

```text
http://localhost:3000
```

## A2A Environment

```env
A2A_HOST=0.0.0.0
A2A_PORT=8050
A2A_PUBLIC_URL=http://a2a-coordinator:8050

A2A_REMOTE_DEFAULT_ENABLED=true
A2A_REMOTE_DEFAULT_NAME=redpa-coordinator
A2A_REMOTE_DEFAULT_URL=http://a2a-coordinator:8050
A2A_REMOTE_DEFAULT_TIMEOUT_SECONDS=30
```

Inside the Docker network, the backend must contact:

```text
http://a2a-coordinator:8050
```

It must not use `localhost:8050`, because `localhost` inside the backend container refers to the backend container itself.

## Dependency Compatibility

The current A2A SDK integration uses Protobuf-based message types.

The project requirements should constrain Protobuf to a compatible major version:

```text
a2a-sdk[http-server]==1.0.2
protobuf>=6,<7
```

## Production Considerations

Before production deployment:

- disable debug mode;
- rotate JWT secrets;
- use managed secrets;
- restrict CORS;
- use TLS;
- remove unnecessary published ports;
- use non-default database credentials;
- add network policies;
- back up PostgreSQL and Qdrant;
- pin image versions;
- configure log retention;
- protect Grafana;
- review Docker socket exposure;
- use least-privilege service accounts;
- restrict Remote Agent allowlists;
- require TLS for external A2A Agents;
- authenticate remote delegation;
- persist Remote Agent configuration;
- add distributed tracing;
- configure A2A retry and circuit-breaker policies.

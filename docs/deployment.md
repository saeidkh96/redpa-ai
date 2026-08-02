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
- Prometheus;
- Grafana.

## Validation

```bash
docker compose config
docker compose ps
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

Prometheus:

```text
http://localhost:9090
```

Grafana:

```text
http://localhost:3000
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
- use least-privilege service accounts.

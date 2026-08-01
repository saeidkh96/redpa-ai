# Deployment

## Local Docker Topology

The Compose stack contains:

- PostgreSQL 17;
- Qdrant;
- RedPA backend;
- Prometheus;
- Grafana.

Ollama runs on the host and is reached through:

```text
http://host.docker.internal:11434
```

## Start

```bash
docker compose up -d --build
```

## Inspect

```bash
docker compose ps
docker compose logs -f backend
```

## Migrations

```bash
docker compose exec backend alembic -c alembic.ini upgrade head
```

## Stop

```bash
docker compose down
```

Remove volumes only when data loss is acceptable:

```bash
docker compose down -v
```

## Ports

| Component | Port |
|---|---:|
| Backend | 8000 |
| PostgreSQL | 5432 |
| Qdrant HTTP | 6333 |
| Qdrant gRPC | 6334 |
| Prometheus | 9090 |
| Grafana | 3000 |

## Production Hardening

- do not embed secrets in Compose;
- rotate JWT and database credentials;
- set `DEBUG=false`;
- restrict CORS;
- avoid publishing PostgreSQL and Qdrant;
- add TLS;
- pin image versions;
- define resource limits;
- configure backups;
- secure Grafana and Prometheus;
- centralize logs;
- control migration execution.

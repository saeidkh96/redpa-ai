# Deployment

## Local Docker Topology

The current Compose stack contains:

- PostgreSQL 17;
- Qdrant;
- RedPA AI backend;
- Prometheus;
- Grafana.

Ollama runs on the host and is reached by the backend container through:

```text
http://host.docker.internal:11434
```

## Start

```bash
docker compose up --build
```

Detached mode:

```bash
docker compose up -d --build
```

Inspect:

```bash
docker compose ps
docker compose logs -f backend
```

Stop:

```bash
docker compose down
```

Remove local volumes only when data loss is acceptable:

```bash
docker compose down -v
```

## Ports

| Component | Host port |
|---|---:|
| Backend | 8000 |
| PostgreSQL | 5432 |
| Qdrant HTTP | 6333 |
| Qdrant gRPC | 6334 |
| Prometheus | 9090 |
| Grafana | 3000 |

## Production Hardening

The current configuration is development-oriented. For production:

- do not embed secrets in Compose;
- rotate JWT and database credentials;
- set `DEBUG=false`;
- restrict CORS to real application origins;
- do not publish PostgreSQL or Qdrant unless required;
- add TLS through a reverse proxy or ingress;
- pin image versions rather than using `latest`;
- enforce CPU and memory limits;
- define restart and health policies;
- use managed or backed-up volumes;
- add database and Qdrant backup procedures;
- secure Grafana and Prometheus;
- use centralized logs;
- use a production ASGI process model;
- define migration execution as a controlled deployment step.

## Ollama Deployment Options

1. **Host-based local development:** current setup.
2. **Separate GPU host:** configure `OLLAMA_BASE_URL`.
3. **Containerized Ollama:** add a service and GPU configuration.
4. **Cloud LLM provider:** implement another provider behind the LLM service abstraction.

## Secret Generation

Example JWT secret generation:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

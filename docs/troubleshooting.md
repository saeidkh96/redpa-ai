# Troubleshooting

## Backend Cannot Reach Ollama

Check:

```bash
ollama serve
ollama list
```

The Docker backend expects Ollama at:

```text
http://host.docker.internal:11434
```

Confirm the model exists:

```bash
ollama pull qwen2.5:7b
```

## PostgreSQL Timeout

```bash
docker compose ps
docker compose logs postgres
```

Confirm the database is healthy and that the backend uses the Compose hostname `postgres`, not `localhost`.

## Qdrant Unavailable

```bash
docker compose logs qdrant
curl http://localhost:6333/healthz
```

Inside the Compose network, the backend should use `http://qdrant:6333`.

## Migration Failure

Check migration state:

```bash
alembic current
alembic history
```

Apply:

```bash
alembic upgrade head
```

Do not delete migration files after they have been shared or deployed.

## Unauthorized

- authenticate again;
- ensure the header starts with `Bearer `;
- check token expiry;
- ensure all running instances share the same JWT secret.

## Planner Produces an Invalid Route

- inspect the raw planner output;
- validate it against the planner schema;
- normalize route aliases;
- apply a deterministic fallback;
- log the planner decision without logging sensitive prompts.

## Grafana Has No Data

- open Prometheus targets;
- confirm the backend metrics target is `UP`;
- check the configured scrape path;
- verify Grafana's provisioned Prometheus URL;
- generate some API traffic.

# Troubleshooting

## Backend Restarting

```bash
docker compose ps
docker compose logs --tail=200 backend
```

Common causes:

- import errors;
- syntax errors;
- circular imports;
- missing environment variables;
- database connection failures;
- invalid module paths.

## Ollama

```bash
ollama serve
ollama list
ollama ps
```

The backend expects:

```text
http://host.docker.internal:11434
```

## PostgreSQL

```bash
docker compose logs postgres
```

The backend should use the Compose hostname `postgres`, not `localhost`.

## Qdrant

```bash
docker compose logs qdrant
```

The backend should use:

```text
http://qdrant:6333
```

## Brave Search

Check without printing the key:

```bash
docker compose exec backend python -c "import os; print('configured' if os.getenv('BRAVE_SEARCH_API_KEY') else 'missing')"
```

## Migration Failure

```bash
docker compose exec backend alembic -c alembic.ini current
docker compose exec backend alembic -c alembic.ini history
docker compose exec backend alembic -c alembic.ini upgrade head
```

## Git Push Rejected

```bash
git pull --rebase origin main
git push origin main
```

Avoid force push unless the consequences are fully understood.

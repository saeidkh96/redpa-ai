# Deployment and Troubleshooting

## Start

```bash
docker compose up -d --build
```

## Migrations

```bash
docker compose exec backend alembic -c alembic.ini upgrade head
```

## Logs

```bash
docker compose ps
docker compose logs --tail=200 backend
```

## Backend Restarting

Common causes:

- import errors;
- circular imports;
- missing environment variables;
- database connection errors;
- invalid module paths.

## Circular Imports

Tools must not import `ToolService` or the registry. The service calls tools; tools do not call the service.

## Ollama

```bash
ollama list
ollama ps
```

Test from Docker:

```bash
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags').read().decode())"
```

## Git Push Rejected

```bash
git pull --rebase origin main
git push origin main
```

Avoid force push unless the consequences are fully understood.

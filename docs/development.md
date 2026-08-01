# Development Guide

## Setup

```bash
python -m venv .venv
pip install -r requirements.txt
docker compose up -d postgres qdrant
```

Apply migrations:

```bash
docker compose exec backend alembic -c alembic.ini upgrade head
```

## Development Rules

- keep API handlers thin;
- put application logic in services;
- keep database access in repositories;
- use Pydantic schemas;
- add migrations for database changes;
- do not call Ollama or Qdrant directly from routes;
- propagate request and workflow identifiers;
- add tests for bug fixes.

## Suggested Checks

```bash
python -m compileall backend/app
pytest
```

Use the actual CI configuration as the final authority.

## Git Hygiene

Do not commit:

- `.env`;
- `.venv`;
- uploaded documents;
- database data;
- Qdrant data;
- Grafana data;
- Python caches;
- IDE secrets.

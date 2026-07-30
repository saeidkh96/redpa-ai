# Development Guide

## Setup

```bash
python -m venv .venv
pip install -r requirements.txt
docker compose up -d postgres qdrant
```

Apply migrations:

```bash
alembic upgrade head
```

Run the API in reload mode using the repository's application import path.

## Development Rules

- keep API handlers thin;
- put application logic in services;
- keep database access in repositories where applicable;
- define request and response contracts with Pydantic schemas;
- add migrations for database changes;
- do not call Ollama or Qdrant directly from route handlers;
- propagate request and workflow identifiers;
- add tests for bug fixes.

## Suggested Checks

```bash
pytest
ruff check .
ruff format --check .
```

Use the commands actually configured in CI as the final authority.

## Git Hygiene

Do not commit:

- `.env`;
- `.venv`;
- uploaded user documents;
- local database data;
- Qdrant data;
- Grafana data;
- Python caches;
- IDE secrets.

The previously generated repository tree included `.venv` and uploaded files. Confirm that they are excluded by `.gitignore` and remove them from Git history if they were committed.

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"


README_CONTENT = r"""# RedPA AI

Production-oriented Agentic AI platform with multi-agent orchestration,
Retrieval-Augmented Generation, MCP tools, A2A specialist agents,
Human-in-the-Loop approval, durable workflows, Agent Memory, background jobs,
distributed tracing, and Kubernetes-ready deployment.

## Core Capabilities

- FastAPI API platform
- JWT authentication
- conversations and messages
- Planner and routing
- RAG with Qdrant
- Human Review and workflow resume
- MCP tool discovery and execution
- A2A Agent Cards and task delegation
- remote specialist agents
- distributed durable workflows
- PostgreSQL long-term Agent Memory
- Qdrant semantic Agent Memory
- shared Agent context
- memory summarization and retention
- Redis distributed cache
- rate limiting
- idempotency keys
- background Worker and Scheduler
- retry and dead-letter queues
- Prometheus and Grafana
- OpenTelemetry and Tempo
- JSON structured logging
- request and correlation IDs
- global error framework
- health, readiness, and liveness
- slow-request and slow-query detection
- Docker Compose
- Kubernetes and Helm

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick Start

```powershell
python -m pip install -r requirements.txt
python -m pytest tests -v
docker compose config
docker compose up -d --build
```

## Main Endpoints

```text
Swagger:       http://localhost:8000/docs
Liveness:      http://localhost:8000/api/v1/platform/live
Readiness:     http://localhost:8000/api/v1/platform/ready
Deep Health:   http://localhost:8000/api/v1/platform/health
Metrics:       http://localhost:8000/api/v1/metrics
Performance:   http://localhost:8000/api/v1/performance/snapshot
```

## Platform Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Qdrant
- Redis
- LangGraph-style orchestration
- MCP
- A2A
- Docker Compose
- Prometheus
- Grafana
- OpenTelemetry
- Tempo
- Kubernetes
- Helm

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Release Checklist](docs/RELEASE_CHECKLIST.md)
- [Portfolio Description](docs/PORTFOLIO.md)
- [Changelog](CHANGELOG.md)

## Release

Current release: `v1.0.0`

## License

MIT License

Copyright (c) 2026 Saeed Khalilian
"""


CHANGELOG_CONTENT = r"""# Changelog

## v1.0.0

### Added

- FastAPI platform architecture;
- JWT authentication;
- conversations and messages;
- Planner, Chat, RAG, Tool, and Human Review workflows;
- MCP servers and unified tool execution;
- A2A coordinator and specialist agents;
- distributed durable workflow persistence and resume;
- PostgreSQL and Qdrant Agent Memory;
- shared Agent context;
- memory summarization, deduplication, and retention;
- Redis cache, rate limiting, and idempotency;
- Worker, Scheduler, retries, and dead-letter jobs;
- Prometheus and Grafana monitoring;
- OpenTelemetry and Tempo tracing;
- security headers and production validation;
- structured JSON logging;
- request IDs, correlation IDs, and error IDs;
- standardized error responses;
- readiness, liveness, and dependency health;
- request and SQL performance monitoring;
- Docker Compose;
- Kubernetes and Helm deployment resources.
"""


def update_gitignore() -> None:
    existing = (
        GITIGNORE.read_text(
            encoding="utf-8",
        )
        if GITIGNORE.exists()
        else ""
    )

    required = [
        ".env",
        ".env.*",
        "!.env.example",
        ".venv/",
        "__pycache__/",
        "*.pyc",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        "dist/",
        "release-check-report.json",
        "*.log",
        ".idea/",
        ".vscode/",
    ]

    lines = existing.splitlines()

    for entry in required:
        if entry not in lines:
            lines.append(entry)

    GITIGNORE.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    README.write_text(
        README_CONTENT,
        encoding="utf-8",
    )

    (
        ROOT / "CHANGELOG.md"
    ).write_text(
        CHANGELOG_CONTENT,
        encoding="utf-8",
    )

    update_gitignore()

    print(
        "Phase 9.6 documentation and release files installed."
    )


if __name__ == "__main__":
    main()

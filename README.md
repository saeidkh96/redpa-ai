# RedPA AI

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

Copyright (c) 2026 Saeid Khalilian

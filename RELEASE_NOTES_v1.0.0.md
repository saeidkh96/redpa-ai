# RedPA AI v1.0.0

RedPA AI v1.0.0 is the first production-oriented release of the platform.

## Highlights

- Multi-agent orchestration
- RAG and document retrieval
- MCP tool platform
- A2A specialist agents
- Human-in-the-Loop approval
- Durable workflow persistence and resume
- Long-term and semantic Agent Memory
- Redis caching and idempotency
- Background Worker, Scheduler, retries, and dead-letter jobs
- Prometheus, Grafana, OpenTelemetry, and Tempo
- Structured logging and standardized errors
- Dependency health and performance monitoring
- Docker Compose, Kubernetes, and Helm

## Validation

Before publishing the release:

```powershell
python scripts/final_release_check.py
python scripts/create_release_archive.py
```

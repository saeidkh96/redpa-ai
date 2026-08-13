# RedPA AI v2.0.0

## Overview

RedPA AI v2 turns the v1 production-oriented backend into an operator-facing Agentic AI control plane.

## New in v2

- Next.js + TypeScript Control Center
- Agent Control Center and capability discovery
- Durable Workflow Visualizer
- Human Review Console with approve, reject, and resume
- Agent Memory Explorer with semantic search and deletion
- authenticated MCP server and tool console
- direct qualified MCP tool execution
- Observability & Operations workspace
- Security & Production Readiness workspace
- V2 Release Readiness panel

## Existing platform foundations

FastAPI, LangGraph, PostgreSQL, Qdrant, Redis, Ollama, MCP, A2A specialist agents,
durable workflows, background jobs, Prometheus, Grafana, OpenTelemetry, Tempo,
Docker Compose, Kubernetes, Helm and GitHub Actions.

## Upgrade notes

The new frontend runs on port `3001`. Grafana remains on `3000`.

## Final verification

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v2\VERIFY_V2_RELEASE.ps1
```

The final v2.0.0 release verification completed successfully with:

- **148 automated tests passed**
- Python source compilation passed
- Docker Compose validation passed
- Liveness, readiness, and deep platform health passed
- Performance snapshot and Prometheus metrics passed
- Control Center availability passed
- JWT authentication passed
- MCP unauthenticated-access boundary passed
- Authenticated MCP control plane passed
- Frontend production image build passed


After the release gate passes and manual checks are complete:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v2\BUILD_V2_RELEASE.ps1
```

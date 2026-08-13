# RedPA AI V6.0 Release Audit

## Scope
This audit is based on files present in the V6.0 source tree. It distinguishes implemented repository surfaces from roadmap claims.

## Implementation evidence

| Capability | Status | Repository evidence |
|---|---|---|
| FastAPI API | Implemented | `backend/app/main.py, backend/app/api/v1` |
| JWT/Auth | Implemented | `backend/app/api/v1/auth.py, backend/app/core/security.py` |
| Agent registry/discovery | Implemented | `backend/app/api/v1/agents.py` |
| Durable distributed workflows | Implemented | `backend/app/api/v1/durable_workflows.py, backend/app/distributed_durable` |
| Human review | Implemented | `backend/app/api/v1/reviews.py` |
| MCP runtime | Implemented | `backend/app/api/v1/mcp.py, backend/app/mcp` |
| A2A | Implemented | `backend/app/a2a` |
| Model gateway | Implemented | `backend/app/model_gateway` |
| Agent memory | Implemented | `backend/app/agent_memory` |
| Evaluation | Implemented | `backend/app/api/v1/evaluations.py` |
| Reliability | Implemented | `backend/app/model_gateway/reliability.py` |
| PostgreSQL persistence | Implemented | `backend/app/database, backend/app/repositories, backend/app/models` |
| Qdrant/RAG | Implemented | `backend/app/health/checks.py, backend/app/health/service.py, backend/app/services/workflow_resume_service.py` |
| Redis/background runtime | Implemented | `backend/app/background_jobs, backend/app/runtime_cache` |
| Prometheus/Grafana/Tempo | Implemented | `docker-compose.yml, observability` |
| Next.js Control Plane | Implemented | `frontend/app/control-plane` |
| Python SDK/CLI | Implemented | `sdk/python/src/redpa_sdk/client.py, sdk/python/src/redpa_sdk/cli.py` |
| Async Python SDK | Implemented | `sdk/python/src/redpa_sdk/async_client.py` |
| SDK CI | Implemented | `.github/workflows/sdk-ci.yml` |
| Kubernetes/Helm | Implemented | `deploy` |
| Azure/Pulumi reference | Implemented | `infra, docs/cloud` |

## Release consistency changes

- Backend default `APP_VERSION` aligned to `6.0.0`.
- Docker Compose backend `APP_VERSION` default aligned to `6.0.0`.
- Frontend package version aligned to `6.0.0`.
- Python SDK package/version remains `6.0.0`.
- Historical V5.5 changelog entry is no longer marked in progress.

## Claim policy

README and release documentation should describe only capabilities backed by repository implementation or deployment/reference assets. Reference infrastructure such as Azure/Pulumi must remain labeled as reference architecture unless deployment evidence exists.

## Runtime validation already observed

- Full Python suite: 298 tests passed on the user's V6 checkout before this release-hardening patch.
- Secret scan passed.
- SDK 6.0.0 built and installed successfully.
- CLI surfaces for workflows, reviews, and MCP were registered successfully.

After applying this patch, rerun the release gate because version metadata changed.

## Release version override hardening

Docker Compose pins backend `APP_VERSION` to `6.0.0` for the tagged V6 release. This prevents a stale developer `.env` value (for example `0.2.0`) from silently overriding the release identity at runtime.

# RedPA AI v3 Final Checklist

## Runtime
- [x] FastAPI
- [x] PostgreSQL
- [x] Qdrant
- [x] Redis
- [x] frontend
- [x] Spring Boot Policy Service

## Agentic platform
- [x] Planner / routing
- [x] RAG
- [x] MCP
- [x] A2A
- [x] durable workflows
- [x] Human Review
- [x] memory

## v3 engineering
- [x] evaluation
- [x] Model Gateway
- [x] policy engine
- [x] DDD / C4 / arc42
- [x] Azure / Pulumi
- [x] RBAC / multi-tenancy
- [x] OAuth PKCE foundation
- [x] event outbox / Redis Streams
- [x] production hardening

## Release gate
- [x] apply final database migration in Docker
- [x] run full regression suite
- [x] run frontend production build
- [x] run Spring Boot build
- [x] run runtime health checks
- [x] run event Redis Streams smoke test
- [x] create release archive
- [x] review archive contents
- [ ] tag v3.0.0 only after all checks pass

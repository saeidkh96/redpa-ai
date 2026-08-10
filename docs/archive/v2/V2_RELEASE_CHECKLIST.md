# RedPA AI v2 Release Checklist

## Functional

- [x] Control Center returns HTTP 200 on port 3001
- [x] Agent registry and capability discovery work
- [x] Workflow Visualizer displays persisted workflows
- [x] Human Review approve / reject / resume works
- [x] Memory create / list / semantic search / delete works
- [x] MCP registry and tool catalog load after login
- [x] At least one safe MCP tool executes from the UI
- [x] Operations page reports health and performance

## Platform

- [x] Liveness passes
- [x] Readiness passes
- [x] Deep health is healthy
- [x] Performance snapshot passes
- [x] Prometheus metrics return HTTP 200
- [x] Worker and Scheduler heartbeats are healthy
- [x] PostgreSQL, Redis and Qdrant are healthy
- [x] Tempo and OpenTelemetry Collector are healthy

## Security

- [x] MCP endpoints reject unauthenticated access
- [x] Human Review endpoints require JWT authentication
- [ ] No real credentials are committed
- [ ] Production secrets are strong and environment-managed
- [ ] DEBUG is disabled in production
- [ ] Detailed errors are disabled in production
- [ ] HTTPS/TLS is enabled in production
- [ ] Hosts and CORS origins are restricted
- [x] Safe/read-only MCP policies are preserved

## Engineering

- [x] Python source compiles
- [ ] pytest passes
- [x] Docker Compose validates
- [x] Frontend production image builds
- [ ] README reflects v2
- [ ] CHANGELOG reflects v2
- [x] docs/archive/v2/RELEASE_NOTES_v2.0.0.md exists
- [ ] Release archive and SHA256 checksum are generated
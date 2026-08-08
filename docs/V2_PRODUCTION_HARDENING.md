# RedPA AI v2 Production Hardening

## Production environment

Use:

```env
ENVIRONMENT=production
DEBUG=false
JSON_LOGS=true
EXPOSE_ERROR_DETAILS=false
REQUIRE_HTTPS=true
```

Use strong environment-managed secrets for application and JWT signing. Restrict
`ALLOWED_HOSTS` and CORS to actual production domains.

## Network and state

Keep PostgreSQL, Redis, Qdrant, MCP services and telemetry components on private
networks unless they explicitly require ingress. Use persistent volumes, backups,
restart policies, health probes and resource limits.

## Tool security

Keep MCP surfaces narrow. Filesystem, GitHub, PostgreSQL and Docker integrations
should remain limited to the explicitly supported safe/read-only operations rather
than becoming generic administrative proxies.

## Observability

Protect Grafana, Prometheus and Tempo outside local development. Review access,
retention and operational-data sensitivity.

## Release gate

Do not tag `v2.0.0` until `VERIFY_V2_RELEASE.ps1` passes and the manual checklist
in `docs/V2_RELEASE_CHECKLIST.md` is reviewed.

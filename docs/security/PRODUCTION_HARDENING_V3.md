# Production Hardening v3

Phase 18 adds a production hardening gate.

## Required production controls

- `DEBUG=false`
- `EXPOSE_ERROR_DETAILS=false`
- `REQUIRE_HTTPS=true`
- strong JWT secret
- explicit allowed hosts
- no wildcard CORS
- managed database / cache / vector credentials
- network isolation
- policy enforcement for side effects
- tenant-scoped authorization
- audit trails
- backups and restore drills
- dependency and container scanning
- metrics, logs, and traces
- change review before production deployment

## Kubernetes

`deploy/kubernetes/network-policy-phase18.yaml` provides a baseline default-deny
network policy plus explicit backend egress ports.

It is a reference baseline; labels and namespace topology must be validated for
the actual target cluster.

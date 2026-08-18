# RedPA AI V18.1 — Production Hardening & Release Validation

## Stage 1 — Cross-version integration
Verify the V12 self-healing, V13 adaptive governance, V14 compliance,
V15 cloud readiness, V16 evaluation, V17 connector governance, and V18 trust
boundaries operate as one platform.

## Stage 2 — Migration chain
Validate database migration continuity through `v260a1b2c3d4e` from a clean baseline.

## Stage 3 — Authenticated API E2E
Exercise real authenticated flows across the production-facing APIs.

## Stage 4 — Persistence and restart
Verify persisted state and idempotency survive backend process restart.

## Stage 5 — Failure injection
Inject controlled operational failures and verify fail-closed behavior.

## Stage 6 — Security boundaries
Verify HITL approval, policy, connector write, and trusted-agent routing boundaries.

## Stage 7 — Docker runtime
Validate required services and backend health.

## Stage 8 — Observability
Verify metrics, logs, and traces are present for production paths.

## Stage 9 — Release evidence
Generate persisted, exportable, machine-readable validation evidence.

## Stage 10 — Regression gate
Require the complete test baseline and all previous hardening gates to pass.

This release hardening layer is evidence-oriented. It does not claim production
readiness solely from architecture or unit-test presence.

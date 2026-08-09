# RedPA AI v3 — Phases 17, 18 and 19

This package closes the planned RedPA v3 roadmap.

## Phase 17 — Event-driven Integrations / Messaging

- Event contracts
- Transactional Outbox
- Redis Streams
- retryable failed publication
- correlation / causation metadata
- authenticated Events API
- Event & Integration Control Center

## Phase 18 — Production Hardening / Security

- production configuration validation
- strong secret requirement
- HTTPS / host / CORS gates
- repository secret scan
- dependency-audit CI
- v3 threat model
- Kubernetes NetworkPolicy baseline

## Phase 19 — Portfolio / Docs / Release v3

- v3 release notes
- capability matrix
- portfolio summary
- final checklist
- release manifest
- reproducible release ZIP
- SHA256
- GitHub release gate

`README.md` is intentionally not modified.

## 1. Extract and apply

```powershell
powershell -ExecutionPolicy Bypass -File .\APPLY_V3_PHASES_17_18_19.ps1
```

## 2. Source verification

```powershell
powershell -ExecutionPolicy Bypass -File .\VERIFY_V3_PHASES_17_18_19_SOURCE.ps1
```

## 3. Apply Docker database migration

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.phase13.yml `
  exec backend alembic upgrade head
```

Verify:

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.phase13.yml `
  exec backend alembic current
```

Expected:

```text
p17a1b2c3d4e (head)
```

## 4. Rebuild runtime

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.phase13.yml `
  up -d --build --force-recreate backend frontend policy-service
```

Open the event UI:

```text
http://localhost:3001/events
```

## 5. Final runtime/release verification

```powershell
powershell -ExecutionPolicy Bypass -File .\VERIFY_V3_PHASES_17_18_19_RUNTIME.ps1
```

Expected final state:

```text
PHASE 17 COMPLETE
PHASE 18 COMPLETE
PHASE 19 COMPLETE
REDPA AI V3 ROADMAP COMPLETE
```

The final verifier also creates:

```text
dist/redpa-ai-v3.0.0.zip
dist/redpa-ai-v3.0.0.sha256
```

Review the archive before creating a `v3.0.0` Git tag.

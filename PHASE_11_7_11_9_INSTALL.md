# RedPA AI v3 — Phase 11.7 / 11.8 / 11.9

Extract this package into the repository root and replace existing Phase 11 files.

Rebuild backend/frontend:

```powershell
docker compose up -d --build --force-recreate backend frontend
```

The database should already be at:

```text
e11a1b2c3d4e
```

Verify it:

```powershell
docker compose exec backend alembic current
```

If needed:

```powershell
docker compose exec backend alembic upgrade head
```

Run final Phase 11 verification:

```powershell
powershell -ExecutionPolicy Bypass -File .\VERIFY_V3_PHASE_11.ps1
```

Expected final message:

```text
PHASE 11 COMPLETE
```

Useful endpoints:

```text
GET  /api/v1/evaluations
POST /api/v1/evaluations
GET  /api/v1/evaluations/metrics
GET  /api/v1/evaluations/observability
POST /api/v1/evaluations/benchmarks/run
POST /api/v1/evaluations/benchmarks/compare
```

Dashboard:

```text
http://localhost:3001/evaluations
```

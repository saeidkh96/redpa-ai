# RedPA AI v3 — Phase 11.4 / 11.5 / 11.6

## 11.4 Benchmark Engine
- Benchmark cases
- Batch evaluation
- Aggregate benchmark score
- Pass rate
- Per-metric averages
- Model/agent comparison ranking

## 11.5 Evaluation API
Adds:
- `POST /api/v1/evaluations`
- `GET /api/v1/evaluations`
- `GET /api/v1/evaluations/metrics`
- `GET /api/v1/evaluations/{run_id}`
- `POST /api/v1/evaluations/benchmarks/run`
- `POST /api/v1/evaluations/benchmarks/compare`

Run the router patch once:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\APPLY_V3_11_5_API.ps1
```

## 11.6 Evaluation Dashboard
Adds:

```text
http://localhost:3001/evaluations
```

The dashboard displays persisted evaluation runs, aggregate scores, metric-level scores, and a JSON runner for creating evaluations.

## Verification

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\VERIFY_V3_11_4_11_6.ps1
```

Then rebuild/restart:

```powershell
docker compose up -d --build --force-recreate backend frontend
```

Smoke test:

```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/evaluations/metrics"
Invoke-WebRequest "http://localhost:3001/evaluations" -UseBasicParsing
```

Note: if the API is protected by your global JWT policy, browser/API requests must use the same authenticated session strategy already used by the v2 Control Center.

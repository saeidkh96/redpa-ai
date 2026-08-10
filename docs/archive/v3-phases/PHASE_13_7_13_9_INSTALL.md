# RedPA AI v3 — Phase 13.7 / 13.8 / 13.9

## 13.7 Policy Control Center

New frontend route:

```text
http://localhost:3001/policy
```

It uses the same `redpa_access_token` local-storage key as the existing RedPA
Control Center.

Features:

- ALLOW / REVIEW / DENY counters;
- CRITICAL-risk counter;
- persisted policy audit table;
- matched rule visibility;
- Human Review ID visibility;
- live authenticated policy enforcement preview.

## 13.8 Security + integration + BDD expansion

Adds tests for:

- DENY cannot be bypassed by `approval_granted`;
- REVIEW fails closed when no review context is available;
- explicit approval can continue a REVIEW path;
- protected policy API dependency contract;
- ALLOW / REVIEW / DENY / unknown BDD policy scenarios.

## 13.9 Final Phase 13 verification

Final verification covers:

- required Phase 13 files;
- Python compilation;
- full pytest suite;
- Alembic head;
- Docker database migration;
- Compose configuration;
- Spring Boot health;
- ALLOW / REVIEW / DENY policy smoke tests;
- Prometheus policy telemetry;
- Policy Control Center HTTP 200;
- frontend production image build.

## Install

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\APPLY_V3_13_7_13_9.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\VERIFY_V3_13_8.ps1
```

Then rebuild frontend:

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.phase13.yml `
  up -d --build --force-recreate frontend
```

Open:

```text
http://localhost:3001/policy
```

Finally:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\VERIFY_V3_PHASE_13.ps1
```

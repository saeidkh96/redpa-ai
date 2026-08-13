# RedPA AI v3 — Phase 16 Complete

Phase 16 covers:

- 16.1 tenant domain;
- 16.2 RBAC;
- 16.3 tenant isolation contracts;
- 16.4 tenant APIs;
- 16.5 OAuth 2.0 Authorization Code + PKCE foundation;
- 16.6 OAuth identity persistence;
- 16.7 Access & Tenancy Control Center;
- 16.8 security tests;
- 16.9 final runtime verification.

## Important OAuth scope

This phase intentionally does **not** fake a complete OAuth login.

A secure OAuth callback requires:

- real provider credentials;
- server-side state persistence;
- PKCE verifier persistence;
- token exchange;
- userinfo verification;
- identity linking rules.

Phase 16 establishes the correct architecture and schema while keeping the
callback non-production until those prerequisites exist.

## Install

Extract into the repository root.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\APPLY_V3_PHASE_16.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\VERIFY_V3_PHASE_16.ps1
```

If source verification passes, apply the migration in Docker:

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.phase13.yml `
  exec backend alembic upgrade head
```

Then rebuild:

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.phase13.yml `
  up -d --build --force-recreate backend frontend
```

Open:

```text
http://localhost:3001/access
```

Finally:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\VERIFY_V3_PHASE_16_RUNTIME.ps1
```

# RedPA AI v3 — Phase 12.7 / 12.8 / 12.9

This package completes Phase 12.

## Install

Extract into the repository root and replace existing Phase 12 files if prompted.

Rebuild the frontend so the new Control Center page exists:

```powershell
docker compose up -d --build --force-recreate frontend
```

Open:

```text
http://localhost:3001/model-gateway
```

The page shows:

- provider registry;
- provider/model health;
- installed models;
- circuit-breaker state;
- routing preview;
- live model invocation;
- normalized token usage and route metadata.

## Final verification

Keep Docker Desktop running and ensure Ollama is reachable.

Then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\VERIFY_V3_PHASE_12.ps1
```

The verification script intentionally asks for a RedPA login because Model Gateway endpoints are protected by the existing JWT boundary.

Expected final line:

```text
PHASE 12 COMPLETE
```

No database migration is required for Phase 12.

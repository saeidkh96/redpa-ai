# RedPA AI V6.0 Repository Cleanup Audit

## Removed from the release candidate

- local runtime uploads under `backend/storage/uploads/` (placeholder retained);
- `.pytest_cache/`;
- Python `__pycache__/` directories and bytecode;
- `frontend/tsconfig.tsbuildinfo`;
- old local `dist/` checksum artifacts;
- empty legacy directories: `v4.1-temp/`, `deployment/`, `infrastructure/`.

## `.gitignore` hardening

- ignores `frontend/tsconfig.tsbuildinfo`;
- preserves only `backend/storage/uploads/.gitkeep` while ignoring runtime upload content.

## Reviewed and intentionally retained

- `BUILD_V3_RELEASE.ps1`, `VERIFY_V3_PHASES_17_18_19_*.ps1`, `RELEASE_MANIFEST_v3.0.0.json`, and `docker-compose.phase13.yml`: still referenced by historical release tests, workflows, README/archive documentation, or source-verification scripts.
- `docs/images/logo.png` and `frontend/public/logo.png`: exact duplicates, but both are retained because they serve different consumers (repository documentation and the Next.js frontend).
- `backend/config/mcp_servers.json` and `backend/config/mcp_servers.example.json`: identical today, but both are retained because the runtime loads the active config while the example file documents the expected configuration shape.
- historical V3/V4/V5 migration and test files: retained because they preserve migration lineage and regression coverage.

## Cleanup policy

No implementation source, migration, active API contract, release test, or referenced historical artifact was removed merely to reduce file count.

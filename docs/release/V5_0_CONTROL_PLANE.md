# RedPA AI V5.0 — Control Plane

V5.0 turns the existing RedPA platform APIs into a unified operator-facing Control Plane.

## Added

- Control Plane shell and navigation;
- platform overview;
- agent registry and health view;
- model/provider health, discovery and circuit view;
- unified Tools & MCP console;
- durable workflow console;
- Human Review console;
- execution explorer over persisted distributed-agent runs;
- Agent Memory analytics and semantic search;
- tenant Usage & Cost view backed by model-governance accounting;
- policy enforcement and audit view;
- tenant and OAuth-provider access view.

## Implementation rule

V5.0 surfaces existing backend behavior rather than presenting roadmap features as implemented. Protected views use the existing RedPA access-token mechanism.

## Verification

The frontend should be verified with:

```bash
cd frontend
npm install
npm run build
```

The repository security scan should be run from a Git checkout:

```bash
python scripts/security/secret_scan.py
```

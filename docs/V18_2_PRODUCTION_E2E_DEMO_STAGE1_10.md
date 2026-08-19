# RedPA AI V18.2 — Production E2E Demonstration

V18.2 turns the production-hardening architecture into a reproducible executable demo. It intentionally uses the existing remote A2A runtime instead of a mocked agent call.

## Stage 1–10

1. Runtime discovery — initialize the existing remote A2A registry.
2. Primary routing — resolve a live primary Agent Card.
3. Trusted-agent boundary — require a live Agent Card from a connected agent shipped in the RedPA Compose runtime; the demo does not fabricate V18 signed-manifest/provenance evidence.
4. Governance boundary — require explicit approval for destructive demo tasks.
5. Failure injection — inject a controlled primary-path failure without killing production containers.
6. Self-healing fallback — resolve a live fallback A2A agent.
7. Real A2A execution — delegate through the existing `RemoteA2AClient`.
8. Recovery and rejoin — verify a final response on the recovered path.
9. Continuous evaluation — pass the recovered execution through the V16 evaluation gate.
10. Audit evidence — persist a machine-readable JSON report under backend storage.

## Run

With the Docker stack running:

```powershell
python scripts/v182_production_e2e_demo.py
```

Expected final line:

```text
E2E DEMO: PASS
```

The default task is deliberately read-only. Destructive keywords are blocked unless `--approve` is supplied.

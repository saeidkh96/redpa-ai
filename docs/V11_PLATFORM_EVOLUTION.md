# RedPA AI v11.0.0 — Platform Evolution Architecture

## Overview

RedPA AI v11.0.0 extends the V10 Governed Agent Runtime with a persistent Platform Evolution layer.

The V10 runtime answers:

> Can this agent action execute, and what happened throughout its governed lifecycle?

The V11 Platform Evolution layer adds:

> Is the platform reliable, routable, compliant, deployable, promotable, integration-safe, and able to trust participating agents?

## Architectural layers

```text
Control Plane / API Consumers
          |
          v
+-------------------------------+
| FastAPI Platform              |
|                               |
| V10 Governed Agent Runtime    |
| V11 Platform Evolution        |
+---------------+---------------+
                |
     +----------+----------+
     |                     |
     v                     v
Policy Service         Agent Runtime
Spring Boot            Planner / RAG / MCP / A2A
     |                     |
     +----------+----------+
                |
                v
        Operations / HITL
                |
                v
        Persistent Evidence
           PostgreSQL
                |
                v
     Observability / Evaluation
```

## V10 governed execution plane

```text
request
 -> governance run
 -> policy decision
 -> optional BLOCKED state
 -> Human-in-the-Loop approval
 -> RUNNING
 -> execution
 -> recovery verification
 -> COMPLETED
 -> evaluation
```

## V11 platform evolution plane

V11 introduces `platform_evolution_records` as a shared evidence ledger.

Each record contains user identity, milestone version, capability kind, status, summary, structured payload, and creation timestamp.

## Capability layers

- **V11 Autonomous Reliability:** operational health evaluation and governed-remediation recommendation.
- **V12 Self-Healing Multi-Agent:** health-aware failover selection.
- **V13 Adaptive Governance:** policy recommendation with `auto_applied=false`.
- **V14 Compliance Evidence:** completeness validation and missing-field evidence.
- **V15 Production Cloud Readiness:** deterministic readiness scoring.
- **V16 Continuous Evaluation:** candidate-vs-baseline rollout gate.
- **V17 Enterprise Connector Governance:** side-effect and approval-risk assessment.
- **V18 Trusted Agent Registry:** trust semantics for versioned agents.

## Persistence

Primary state:

- PostgreSQL — relational state, governance runs, policy overrides, evolution evidence;
- Qdrant — vector retrieval and semantic memory;
- Redis — streams, caching, and runtime coordination.

## Observability

RedPA combines OpenTelemetry, Tempo, Prometheus, Grafana, application logs, governance events, and evaluation records.

## Control Plane

```text
/control-plane/governance
/control-plane/policy
/control-plane/evolution
```

## Migration chain

```text
v102a1b2c3d4e
 -> v110a1b2c3d4e
 -> v120a1b2c3d4e
 -> v130a1b2c3d4e
 -> v140a1b2c3d4e
 -> v150a1b2c3d4e
 -> v160a1b2c3d4e
 -> v170a1b2c3d4e
 -> v180a1b2c3d4e
```

Current head:

```text
v180a1b2c3d4e
```

## Verified evidence

```text
V11  action_required
V12  routable
V13  recommendation
V14  incomplete
V15  ready
V16  promote
V17  review
V18  trusted
```

V14 `incomplete` was intentional: `evaluation_score` was omitted to validate missing-evidence detection.

## Design boundary

The platform deliberately distinguishes observation, recommendation, policy decision, human approval, execution, verification, and evaluation.

That separation is central to the RedPA production-oriented design.

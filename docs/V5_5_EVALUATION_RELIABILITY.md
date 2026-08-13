# RedPA AI V5.5 — Evaluation & Reliability

## Batch 1: Regression Detection and Quality Gates

V5.5 builds on the existing evaluation, benchmark, telemetry, production-runtime evaluation, and model-gateway reliability subsystems.

Batch 1 adds persisted-run regression analysis and explicit promotion quality gates.

### Implemented

- persisted evaluation baseline vs candidate comparison;
- aggregate-score regression detection;
- per-metric regression detection;
- missing-candidate-metric regression detection;
- configurable aggregate and metric drop thresholds;
- minimum candidate score checks;
- candidate pass-threshold enforcement;
- explicit `PASS` / `FAIL` quality-gate decision;
- Control Plane view for selecting baseline/candidate runs and inspecting metric deltas.

### API

```text
POST /api/v1/evaluations/regression/compare
POST /api/v1/evaluations/quality-gates/evaluate
```

### Control Plane

```text
/control-plane/reliability
```

### Scope

This batch compares persisted evaluation runs already stored by RedPA. It does not claim automated deployment promotion or CI blocking yet; those are separate integrations.

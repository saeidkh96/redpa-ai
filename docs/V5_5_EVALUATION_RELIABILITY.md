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


## Batch 2: Benchmark Persistence and Provider Reliability

Implemented:

- database-backed benchmark run history;
- benchmark filtering by agent or model;
- persisted case results and metric averages;
- provider reliability scorecards derived from live health and circuit-breaker state;
- deterministic retry/fallback failure validation without mutating live providers;
- Control Plane benchmark history and reliability scorecard.

API:

```text
GET  /api/v1/evaluations/benchmark-history
GET  /api/v1/evaluations/benchmark-history/{run_id}
GET  /api/v1/model-gateway/reliability/scorecard
POST /api/v1/model-gateway/reliability/simulate
```

`POST /api/v1/evaluations/benchmarks/run` now persists its benchmark result.

The failure simulator validates retry/fallback policy behavior deterministically. It does not inject faults into external production providers.


## Batch 3: Release Quality Pipeline

Implemented:

- persisted release quality-gate decisions;
- release labels and gate metadata;
- historical PASS/FAIL decisions with reasons and regression evidence;
- CI-friendly quality-gate endpoint that returns HTTP `409` when promotion is blocked;
- benchmark trend history using persisted benchmark runs;
- Control Plane release-gate history and benchmark trend views;
- standalone CI CLI with process exit codes.

API:

```text
POST /api/v1/evaluations/release-gates/evaluate
POST /api/v1/evaluations/release-gates/ci-check
GET  /api/v1/evaluations/release-gates
GET  /api/v1/evaluations/benchmark-trends
```

CI CLI:

```bash
python scripts/quality/release_gate.py \
  --baseline <BASELINE_EVALUATION_UUID> \
  --candidate <CANDIDATE_EVALUATION_UUID> \
  --release-label v5.5-candidate
```

Exit codes:

```text
0  quality gate passed
1  quality gate failed (HTTP 409)
2  request/configuration error
```

This creates a real promotion boundary without claiming that RedPA automatically deploys a candidate after a PASS decision.


## Batch 4: Benchmark Registry and Release Evidence

Implemented:

- persisted benchmark suite registry with reusable evaluation cases;
- execution of a persisted benchmark suite with persisted benchmark results;
- reliability snapshot capture and historical reliability evidence;
- release candidate reports combining candidate evaluation, latest quality gate, matching benchmark evidence, and provider reliability;
- Control Plane views for benchmark suites, reliability history, and release candidate evidence.

API:

```text
POST /api/v1/evaluations/benchmark-suites
GET  /api/v1/evaluations/benchmark-suites
GET  /api/v1/evaluations/benchmark-suites/{suite_id}
POST /api/v1/evaluations/benchmark-suites/{suite_id}/run
GET  /api/v1/evaluations/release-candidates/{candidate_run_id}/report

POST /api/v1/model-gateway/reliability/capture
GET  /api/v1/model-gateway/reliability/history
```

The repository already contains a background-job scheduler, but Batch 4 does not claim scheduled benchmark execution. Persisted suites can be invoked explicitly through the API or CI; scheduler integration remains separate work.

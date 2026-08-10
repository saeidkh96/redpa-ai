# RedPA AI v3 — Phase 11.1 / 11.2 / 11.3

This package adds the Evaluation Core, deterministic baseline metrics, persistence layer, evaluation service, migration, tests, and verification script.

## 11.1 Evaluation Core
- EvaluationRun / EvaluationResult
- EvaluationRunStatus / EvaluationMetric
- Pydantic evaluation schemas
- PostgreSQL persistence
- Alembic revision `e11a1b2c3d4e` based on current head `9b6671617550`

## 11.2 Metrics Engine
- Task Success
- Routing Accuracy
- Tool Selection Accuracy (F1)
- Response Relevance
- RAG Faithfulness
- Context Relevance
- Latency
- Token Usage
- Cost

Text relevance/faithfulness metrics are intentionally deterministic lexical baselines. Later phases can add embedding or LLM-judge implementations behind the same registry interface.

## 11.3 Evaluation Service
- create run
- evaluate selected metrics
- weighted aggregation
- pass/fail thresholds
- persist metric results
- retrieve single/list runs
- failed-run state handling

## Install
Extract into the repository root and replace files when prompted.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\archive\v3-phases\VERIFY_V3_11_1_11_3.ps1
```

If PASS:

```powershell
cd backend
alembic upgrade head
alembic current
cd ..
python -m pytest .\tests -q
```

Expected Alembic revision after migration:

```text
e11a1b2c3d4e
```

No API route or Control Center page is added yet; those belong to later Phase 11 steps.

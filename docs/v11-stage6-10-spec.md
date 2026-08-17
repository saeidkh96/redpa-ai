# V11 Stage 6–10 Specification

## Stage 6 — Failure-Path Validation

Required behavior:

```text
incident
→ diagnosis
→ REVIEW
→ approval
→ remediation attempted
→ recovery verification fails
→ ops.recovery_failed
→ incident = failed
→ governance run = failed
→ incident MUST NOT become resolved
```

Acceptance criteria:

- `wait_until_healthy()` timeout or restart exception produces a failed action.
- incident becomes `failed`.
- governance run becomes `failed`.
- `ops.recovery_failed` exists.
- no `ops.recovery_verified` event exists for the failed attempt.
- no `resolved` state is written.

## Stage 7 — Audit & Evidence Hardening

Recommended canonical lifecycle:

```text
run.created
run.running
ops.diagnosis_started
ops.diagnosis_completed
policy.checked
run.blocked
ops.remediation_blocked
human.approval_granted
run.resumed
policy.checked
ops.remediation_started
ops.recovery_verified
incident.resolved
run.completed
evaluation.completed
```

Minimum event payload fields:

- `incident_id`
- `run_id` where appropriate
- `user_id` / actor when approval is human-driven
- action
- target
- policy decision/risk/reason
- approval state
- timestamp from persisted event record

## Stage 8 — Idempotency & Duplicate Protection

Required invariant:

```text
same incident + same governed action + same approval intent
→ at most one destructive execution
```

Recommended implementation:

- client optional `idempotency_key`
- server-generated deterministic fallback key
- persisted key in remediation action row
- unique DB constraint
- existing completed/in-progress action returned on duplicate
- concurrent duplicate requests must not trigger a second restart

Recommended deterministic key inputs:

```text
incident_id
run_id
action
target
approval=true
```

## Stage 9 — Restart & Persistence Validation

Required scenario:

```text
incident created
→ governance run blocked
→ backend/scheduler restart
→ persisted state reload
→ approval
→ resume
→ remediation
→ completed
```

Acceptance criteria:

- incident persists
- governance run persists
- blocked state persists
- events persist
- scheduler restart does not duplicate incidents
- approval can resume the existing run
- remediation still completes

## Stage 10 — Production Readiness Gate

Command:

```powershell
python scripts/production_validation.py
```

Expected logical output:

```text
[PASS] Stage 6 failure-path safety
[PASS] Stage 7 audit completeness
[PASS] Stage 8 idempotency
[PASS] Stage 9 persistence/restart recovery
[PASS] Stage 10 readiness gate

PRODUCTION VALIDATION: PASS
```

The script also emits JSON evidence to:

```text
artifacts/v11-production-validation.json
```

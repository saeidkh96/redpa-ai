from scripts.production_validation import validate


def _good_evidence():
    return {
        "stage6": {
            "recovery_failed_event": True,
            "incident_status": "failed",
            "run_status": "failed",
            "resolved_written": False,
        },
        "stage7": {
            "events": [
                "ops.remediation_blocked",
                "human.approval_granted",
                "run.resumed",
                "ops.remediation_started",
                "ops.recovery_verified",
                "run.completed",
            ]
        },
        "stage8": {
            "destructive_execution_count": 1,
            "duplicate_detected": True,
        },
        "stage9": {
            "incident_persisted": True,
            "run_persisted": True,
            "events_persisted": True,
            "resumed_after_restart": True,
        },
    }


def test_v11_gate_passes_when_stage6_to_9_pass():
    checks = validate(_good_evidence())
    assert all(check.passed for check in checks)


def test_stage6_fails_if_incident_is_resolved_after_failed_recovery():
    evidence = _good_evidence()
    evidence["stage6"]["resolved_written"] = True
    checks = validate(evidence)
    stage6 = next(c for c in checks if c.name.startswith("Stage 6"))
    assert stage6.passed is False


def test_stage8_fails_on_duplicate_destructive_execution():
    evidence = _good_evidence()
    evidence["stage8"]["destructive_execution_count"] = 2
    checks = validate(evidence)
    stage8 = next(c for c in checks if c.name.startswith("Stage 8"))
    assert stage8.passed is False

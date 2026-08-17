from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def test_stage3_governed_recovery_stops_at_approval_boundary():
    code = read("backend/app/production_validation/coordinator.py")
    assert "start_incident_run" in code
    assert "diagnose_governed" in code
    assert "remediate_governed" in code
    assert "approved=False" in code
    assert "PRODUCTION_VALIDATION_OWNER_USER_ID" in code

def test_stage4_requires_health_verification_before_resolve():
    code = read("backend/app/ops_v9/service.py")
    verify = code.index("wait_until_healthy")
    resolve = code.index("set_incident_status(incident_id, 'resolved')", verify)
    assert verify < resolve
    assert 'event_type="ops.recovery_verified"' in code

def test_stage5_evidence_is_preserved_by_existing_governance_finish():
    bridge = read("backend/app/ops_v9/governance.py")
    assert "evaluate_run" in bridge
    assert "TASK_SUCCESS" in bridge
    assert "evaluation.completed" in read("backend/app/governance_v10/service.py")

def test_scheduler_wires_incident_to_recovery_coordinator():
    runtime = read("backend/app/production_validation/runtime.py")
    assert "prepare_governed_recovery" in runtime
    assert "governance_run=" in runtime

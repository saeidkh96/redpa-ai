from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_ops_v9_exposes_authenticated_governance_run_boundary():
    api = read("backend/app/api/v1/operations_v9.py")
    assert "CurrentUser" in api
    assert "DatabaseSession" in api
    assert "/incidents/{incident_id}/governance-run" in api
    assert "/incidents/{incident_id}/governed/{run_id}/diagnose" in api
    assert "/incidents/{incident_id}/governed/{run_id}/remediate" in api


def test_ops_governance_bridge_creates_run_checks_policy_and_evaluates_recovery():
    bridge = read("backend/app/ops_v9/governance.py")
    assert 'agent_id="redpa-ops-agent"' in bridge
    assert "policy_check" in bridge
    assert 'boundary="ops_remediation"' in bridge
    assert "EvaluationMetric.TASK_SUCCESS" in bridge
    assert 'evaluator_version="v10-phase3-ops"' in bridge


def test_ops_governed_service_traces_diagnosis_hitl_remediation_and_recovery():
    service = read("backend/app/ops_v9/service.py")
    for event in [
        "ops.diagnosis_started",
        "ops.diagnosis_completed",
        "ops.remediation_blocked",
        "ops.remediation_started",
        "ops.recovery_verified",
        "ops.recovery_failed",
    ]:
        assert event in service
    assert "not payload.approved or not policy.executable" in service
    assert "OpsGovernanceBridge.finish" in service


def test_v9_legacy_ops_contract_is_preserved():
    service = read("backend/app/ops_v9/service.py")
    agent = read("backend/app/ops_v9/agent_server.py")
    assert "async def diagnose(cls, incident_id: UUID)" in service
    assert "async def remediate(cls, incident_id: UUID, payload: RemediationRequest)" in service
    assert "_STATEFUL_DENY = {'redpa-postgres','redpa-qdrant','redpa-redis'}" in agent
    assert "if not payload.approved" in agent

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def test_stage6_verification_is_inside_fail_closed_boundary():
    code = read("backend/app/ops_v9/service.py")
    restart = code.index("result = await OpsAgentClient().restart", code.index("remediate_governed"))
    verify = code.index("verification = await OpsAgentClient().wait_until_healthy", restart)
    failure = code.index('event_type="ops.recovery_failed"', verify)
    resolve = code.index("set_incident_status(incident_id, 'resolved')", verify)
    assert restart < verify < failure < resolve

def test_stage7_approval_and_resume_have_explicit_audit_events():
    code = read("backend/app/ops_v9/service.py")
    assert 'event_type="human.approval_granted"' in code
    assert 'event_type="run.resumed"' in code
    assert '"actor_user_id": str(user_id)' in code

def test_stage8_idempotency_is_persisted_and_db_enforced():
    schema = read("backend/app/ops_v9/schemas.py")
    repo = read("backend/app/ops_v9/repository.py")
    migration = read("backend/alembic/versions/v190a1b2c3d4e_v11_ops_validation_hardening.py")
    assert "idempotency_key" in schema
    assert "ON CONFLICT (incident_id, idempotency_key) DO NOTHING" in repo
    assert "duplicate_detected" in repo
    assert "uq_ops_actions_incident_idempotency" in migration

def test_stage9_ops_and_governance_state_are_database_persisted():
    repo = read("backend/app/ops_v9/repository.py")
    governance = read("backend/app/governance_v10/repository.py")
    assert "DATABASE_URL" in repo and "ops_incidents" in repo and "ops_actions" in repo
    assert "AgentRun" in governance and "session" in governance

def test_stage10_machine_readable_gate_is_present():
    gate = read("scripts/production_validation.py")
    assert "PRODUCTION VALIDATION" in gate
    assert "v11-production-validation.json" in gate

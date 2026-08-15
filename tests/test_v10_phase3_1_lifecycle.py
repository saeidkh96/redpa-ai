from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

def test_governance_service_supports_explicit_blocked_resume():
    source = read("backend/app/governance_v10/service.py")
    assert "async def resume_run" in source
    assert "Only blocked runs can be resumed" in source
    assert "AgentRunStatus.BLOCKED" in source
    assert "AgentRunStatus.RUNNING" in source

def test_ops_resumes_after_approved_executable_policy_before_restart():
    source = read("backend/app/ops_v9/service.py")

    governed_start = source.index("async def remediate_governed")
    governed_source = source[governed_start:]

    assert "if payload.approved and policy.executable" in governed_source
    assert "OpsGovernanceBridge.resume_after_approval" in governed_source

    resume_index = governed_source.index(
        "OpsGovernanceBridge.resume_after_approval"
    )
    restart_index = governed_source.index(
        "OpsAgentClient().restart"
    )

    assert resume_index < restart_index

def test_recovery_failure_is_separate_from_governance_finalization_failure():
    source = read("backend/app/ops_v9/service.py")
    assert 'event_type="ops.recovery_verified"' in source
    assert 'event_type="ops.recovery_failed"' in source
    assert 'event_type="ops.governance_finalization_failed"' in source
    assert '"recovery_verified": True' in source

def test_phase31_bridge_calls_resume_run():
    source = read("backend/app/ops_v9/governance.py")
    assert "resume_after_approval" in source
    assert "resume_run" in source

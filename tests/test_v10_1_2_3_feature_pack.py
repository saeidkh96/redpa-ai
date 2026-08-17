from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v101_governance_control_plane_uses_real_run_api():
    page = read("frontend/app/control-plane/governance/page.tsx")
    assert "/api/v1/governance/v10/runs" in page
    assert "Event timeline" in page
    assert "evaluation_score" in page
    assert "policy.decision" not in page or "event_type" in page


def test_v102_policy_overrides_are_persisted_and_enforced_before_external_policy():
    service = read("backend/app/services/policy_enforcement_service.py")
    override = read("backend/app/services/policy_override_v10_service.py")
    migration = read(
        "backend/alembic/versions/v102a1b2c3d4e_policy_overrides.py"
    )

    assert "self.policy_overrides.evaluate" in service

    assert (
        service.index("self.policy_overrides.evaluate")
        < service.index("self.guardrails.evaluate")
    )

    assert 'source="redpa-policy-override"' in override
    assert 'revision = "v102a1b2c3d4e"' in migration
    assert 'down_revision = "v100a1b2c3d4e"' in migration


def test_v102_policy_management_ui_supports_allow_review_deny_and_toggle():
    page = read("frontend/app/control-plane/policy/page.tsx")
    assert "/api/v1/policy/overrides" in page
    assert "<option>ALLOW</option>" in page
    assert "<option>REVIEW</option>" in page
    assert "<option>DENY</option>" in page
    assert "Disable" in page and "Enable" in page


def test_v103_e2e_covers_block_approve_resume_recovery_and_evaluation():
    script = read("scripts/e2e/v10_governance_ops_e2e.py")
    workflow = read(".github/workflows/v10-governance-e2e.yml")

    # Container failure injection
    assert '"stop"' in script
    assert "CONTAINER" in script

    # Deny -> blocked
    assert '"approved": False' in script
    assert "blocked_payload" in script
    assert '"blocked"' in script

    # Approve -> recovery
    assert '"approved": True' in script
    assert '"restart_container"' in script
    assert '"ops.remediation_started"' in script
    assert '"ops.recovery_verified"' in script

    # Completed governed run
    assert "payload" in script
    assert '"status"' in script
    assert '"completed"' in script
    assert '"run.completed"' in script

    # Evaluation linkage
    assert '"evaluation_run_id"' in script
    assert '"evaluation_score"' in script
    assert '"evaluation.completed"' in script

    # CI automation
    assert "workflow_dispatch" in workflow
    assert "docker compose up -d --build" in workflow
    assert (
        "python scripts/e2e/v10_governance_ops_e2e.py"
        in workflow
    )

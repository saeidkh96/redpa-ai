from __future__ import annotations

from pathlib import Path

from app.adaptive_governance_v13.schemas import PolicyProposalCreate
from app.adaptive_governance_v13.validation import validate_v13_evidence


def test_v13_proposal_schema_does_not_expose_auto_apply_input():
    fields = PolicyProposalCreate.model_fields
    assert "auto_applied" not in fields


def test_v13_service_requires_approved_status_before_apply():
    source = Path("backend/app/adaptive_governance_v13/service.py").read_text(encoding="utf-8")
    assert 'if row.status != "approved"' in source
    assert "Only explicitly approved proposals can be applied." in source
    assert 'shadow.get("safe_to_apply")' in source
    assert "row.auto_applied = False" in source


def test_v13_validation_gate_passes_complete_evidence():
    evidence = {
        "stage1": {"signals_persisted": True},
        "stage2": {"history_used": True},
        "stage3": {"recommendation_created": True},
        "stage4": {"risk_scored": True},
        "stage5": {"high_risk_requires_review": True, "auto_applied": False},
        "stage6": {"version_incremented": True},
        "stage7": {"shadow_gate_enforced": True},
        "stage8": {"approved_before_apply": True, "auto_applied": False},
        "stage9": {"rollback_verified": True},
    }
    checks = validate_v13_evidence(evidence)
    assert len(checks) == 10
    assert all(check.passed for check in checks)

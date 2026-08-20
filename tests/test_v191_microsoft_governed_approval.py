from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v191_router_registered():
    router = read("backend/app/api/v1/router.py")

    assert "microsoft_integration_v191_router" in router
    assert "include_router(microsoft_integration_v191_router)" in router


def test_v191_api_contract():
    source = read(
        "backend/app/api/v1/microsoft_integration_v191.py"
    )

    assert "/integrations/microsoft/v19.1" in source
    assert "/power-automate/approval" in source
    assert "/decision" in source


def test_v191_service_uses_existing_human_review():
    source = read(
        "backend/app/microsoft_integration_v191/service.py"
    )

    assert "HumanReviewService.create" in source
    assert "HumanReviewService.approve" in source
    assert "HumanReviewService.reject" in source


def test_v191_governance_events():
    source = read(
        "backend/app/microsoft_integration_v191/service.py"
    )

    assert "approval.requested" in source
    assert "approval.{payload.decision}" in source
    assert "resume_run" in source


def test_v191_no_live_tenant_claim():
    source = read(
        "backend/app/api/v1/microsoft_integration_v191.py"
    )

    assert '"live_tenant_connection": False' in source
    assert '"credentials_embedded": False' in source


def test_v191_decision_updates_approval_metadata():
    source = read(
        "backend/app/microsoft_integration_v191/service.py"
    )

    assert '"approval_required": False' in source
    assert '"approval_granted": True' in source
    assert '"approval_granted": False' in source
    assert '"approved_review_id": str(review.id)' in source
    assert '"approval_decision": "approved"' in source
    assert '"approval_decision": "rejected"' in source

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4
from app.security_compliance_v14.engine import ComplianceEvidenceEngine
from app.security_compliance_v14.hashing import sha256_payload

def control(**overrides):
    data={"control_id":"SEC-001","severity":"high","required_fields":["owner","status"],"required_evidence_types":["runtime"],"approval_required":True}
    data.update(overrides); return SimpleNamespace(**data)

def evidence(payload, **overrides):
    data={"id":uuid4(),"payload":payload,"evidence_type":"runtime","content_hash":sha256_payload(payload),"expires_at":datetime.now(timezone.utc)+timedelta(days=1)}
    data.update(overrides); return SimpleNamespace(**data)

def test_v14_complete_valid_evidence_can_pass():
    result=ComplianceEvidenceEngine.assess(control=control(approval_required=False,severity="medium"),evidence_rows=[evidence({"owner":"platform","status":"healthy"})],strict_integrity=True)
    assert result.status=="pass"

def test_v14_missing_required_field_requires_review():
    result=ComplianceEvidenceEngine.assess(control=control(),evidence_rows=[evidence({"owner":"platform"})],strict_integrity=True)
    assert "status" in result.missing_fields
    assert result.approval_required is True

def test_v14_hash_mismatch_fails_closed():
    result=ComplianceEvidenceEngine.assess(control=control(),evidence_rows=[evidence({"owner":"platform","status":"healthy"},content_hash="0"*64)],strict_integrity=True)
    assert result.status=="fail"

def test_v14_expired_evidence_not_fresh():
    result=ComplianceEvidenceEngine.assess(control=control(),evidence_rows=[evidence({"owner":"platform","status":"healthy"},expires_at=datetime.now(timezone.utc)-timedelta(seconds=1))],strict_integrity=True)
    assert result.freshness_score==0.0

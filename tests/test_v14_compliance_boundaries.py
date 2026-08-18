from pathlib import Path
from app.security_compliance_v14.validation import validate_v14_evidence

def test_v14_review_is_explicit():
    source=Path("backend/app/security_compliance_v14/service.py").read_text(encoding="utf-8")
    assert 'if record.approval_status != "pending"' in source
    assert 'record.approval_status = "approved" if payload.approved else "rejected"' in source

def test_v14_integrity_uses_sha256():
    source=Path("backend/app/security_compliance_v14/hashing.py").read_text(encoding="utf-8")
    assert "hashlib.sha256" in source

def test_v14_gate_passes_good_evidence():
    e={
      "stage1":{"control_versioned":True},"stage2":{"evidence_persisted":True},
      "stage3":{"missing_detected":True},"stage4":{"hash_verified":True},
      "stage5":{"expiry_enforced":True},"stage6":{"risk_scored":True},
      "stage7":{"high_risk_requires_approval":True},"stage8":{"record_persisted":True},
      "stage9":{"export_verified":True},
    }
    checks=validate_v14_evidence(e)
    assert len(checks)==10 and all(c.passed for c in checks)

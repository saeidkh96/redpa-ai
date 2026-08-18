from __future__ import annotations
from datetime import datetime, timezone
from app.security_compliance_v14.hashing import sha256_payload
from app.security_compliance_v14.schemas import EvidenceAssessmentResponse, EvidenceFinding

class ComplianceEvidenceEngine:
    @staticmethod
    def assess(*, control, evidence_rows, strict_integrity: bool) -> EvidenceAssessmentResponse:
        required_fields = set(control.required_fields or [])
        required_types = set(control.required_evidence_types or [])
        present_fields, present_types = set(), set()
        integrity_ok = fresh_ok = 0
        findings = []
        now = datetime.now(timezone.utc)

        for evidence in evidence_rows:
            present_fields.update((evidence.payload or {}).keys())
            present_types.add(evidence.evidence_type)
            if sha256_payload(evidence.payload or {}) == evidence.content_hash:
                integrity_ok += 1
            else:
                findings.append(EvidenceFinding(code="HASH_MISMATCH", message=f"Evidence {evidence.id} failed integrity verification.", severity="critical" if strict_integrity else "high"))
            if not evidence.expires_at or evidence.expires_at > now:
                fresh_ok += 1
            else:
                findings.append(EvidenceFinding(code="EVIDENCE_EXPIRED", message=f"Evidence {evidence.id} is expired.", severity="high"))

        missing_fields = sorted(required_fields - present_fields)
        missing_types = sorted(required_types - present_types)

        for name in missing_fields:
            findings.append(EvidenceFinding(code="MISSING_FIELD", message=f"Required evidence field '{name}' is missing.", severity=control.severity))
        for name in missing_types:
            findings.append(EvidenceFinding(code="MISSING_EVIDENCE_TYPE", message=f"Required evidence type '{name}' is missing.", severity=control.severity))

        denom = max(len(required_fields) + len(required_types), 1)
        complete_num = (len(required_fields) - len(missing_fields)) + (len(required_types) - len(missing_types))
        completeness = max(0.0, min(1.0, complete_num / denom))
        integrity = integrity_ok / max(len(evidence_rows), 1)
        freshness = fresh_ok / max(len(evidence_rows), 1)

        severity_weight = {"low": 0.15, "medium": 0.35, "high": 0.65, "critical": 0.90}[control.severity]
        risk = round(max(0.0, min(1.0, (1-completeness)*0.40 + (1-integrity)*0.35 + (1-freshness)*0.15 + severity_weight*0.10)), 4)

        if strict_integrity and integrity < 1.0:
            status = "fail"
        elif completeness < 1.0 or freshness < 1.0 or risk >= 0.35:
            status = "review"
        else:
            status = "pass"

        approval_required = bool(control.approval_required or status != "pass" or control.severity in {"high", "critical"})
        return EvidenceAssessmentResponse(
            control_id=control.control_id,
            status=status,
            completeness_score=round(completeness,4),
            integrity_score=round(integrity,4),
            freshness_score=round(freshness,4),
            risk_score=risk,
            missing_fields=missing_fields,
            missing_evidence_types=missing_types,
            findings=findings,
            approval_required=approval_required,
        )

compliance_evidence_engine = ComplianceEvidenceEngine()

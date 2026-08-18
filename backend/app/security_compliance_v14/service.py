from __future__ import annotations
from datetime import datetime, timezone
from app.security_compliance_v14.engine import compliance_evidence_engine
from app.security_compliance_v14.hashing import sha256_payload
from app.security_compliance_v14.repository import SecurityComplianceRepository

class ControlNotFoundError(LookupError): pass
class ComplianceRecordNotFoundError(LookupError): pass
class InvalidComplianceTransitionError(RuntimeError): pass

class SecurityComplianceService:
    async def create_control(self, *, session, user_id, payload):
        return await SecurityComplianceRepository.create_control(session=session,user_id=user_id,payload=payload)

    async def collect_evidence(self, *, session, user_id, payload):
        control = await SecurityComplianceRepository.latest_control(session=session,user_id=user_id,control_id=payload.control_id)
        if control is None: raise ControlNotFoundError(f"Compliance control '{payload.control_id}' was not found.")
        return await SecurityComplianceRepository.create_evidence(session=session,user_id=user_id,payload=payload)

    async def verify_evidence(self, *, session, user_id, evidence_id):
        rows = await SecurityComplianceRepository.get_evidence(session=session,user_id=user_id,evidence_ids=[evidence_id])
        if not rows: raise LookupError(f"Evidence '{evidence_id}' was not found.")
        row = rows[0]
        row.status = "invalid" if sha256_payload(row.payload or {}) != row.content_hash else ("expired" if row.expires_at and row.expires_at <= datetime.now(timezone.utc) else "verified")
        row.verified_at = datetime.now(timezone.utc)
        return await SecurityComplianceRepository.save_evidence(session=session,row=row)

    async def assess(self, *, session, user_id, payload):
        control = await SecurityComplianceRepository.latest_control(session=session,user_id=user_id,control_id=payload.control_id)
        if control is None: raise ControlNotFoundError(f"Compliance control '{payload.control_id}' was not found.")
        evidence_rows = await SecurityComplianceRepository.get_evidence(session=session,user_id=user_id,evidence_ids=payload.evidence_ids)
        if len(evidence_rows) != len(set(payload.evidence_ids)): raise ValueError("One or more evidence items were not found.")
        assessment = compliance_evidence_engine.assess(control=control,evidence_rows=evidence_rows,strict_integrity=payload.strict_integrity)
        snapshot = [{"id":str(e.id),"control_id":e.control_id,"evidence_type":e.evidence_type,"source":e.source,"subject":e.subject,"status":e.status,"content_hash":e.content_hash,"collected_at":e.collected_at.isoformat(),"expires_at":e.expires_at.isoformat() if e.expires_at else None} for e in evidence_rows]
        record = await SecurityComplianceRepository.create_record(session=session,user_id=user_id,control_id=payload.control_id,assessment_status=assessment.status,approval_status="pending" if assessment.approval_required else "not_required",assessment=assessment.model_dump(mode="json"),evidence_snapshot=snapshot)
        return assessment, record

    async def approve_record(self, *, session, user_id, reviewer_id, record_id, payload):
        record = await SecurityComplianceRepository.get_record(session=session,user_id=user_id,record_id=record_id)
        if record is None: raise ComplianceRecordNotFoundError(f"Compliance record '{record_id}' was not found.")
        if record.approval_status != "pending": raise InvalidComplianceTransitionError(f"Compliance record in approval status '{record.approval_status}' cannot be reviewed.")
        record.approval_status = "approved" if payload.approved else "rejected"
        record.approved_by = reviewer_id if payload.approved else None
        record.approved_at = datetime.now(timezone.utc)
        record.assessment = {**(record.assessment or {}), "review_reason": payload.reason}
        return await SecurityComplianceRepository.save_record(session=session,row=record)

security_compliance_service = SecurityComplianceService()

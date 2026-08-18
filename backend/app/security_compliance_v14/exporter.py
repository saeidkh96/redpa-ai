from __future__ import annotations
class ComplianceRecordExporter:
    @staticmethod
    def export(record):
        return {
            "record_id": str(record.id),
            "control_id": record.control_id,
            "assessment_status": record.assessment_status,
            "approval_status": record.approval_status,
            "assessment": record.assessment,
            "evidence_snapshot": record.evidence_snapshot,
            "approved_by": str(record.approved_by) if record.approved_by else None,
            "approved_at": record.approved_at.isoformat() if record.approved_at else None,
            "created_at": record.created_at.isoformat(),
        }
compliance_record_exporter = ComplianceRecordExporter()

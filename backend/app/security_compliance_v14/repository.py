from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.security_compliance_v14 import ComplianceControl, ComplianceEvidence, ComplianceRecord
from app.security_compliance_v14.hashing import sha256_payload

class SecurityComplianceRepository:
    @staticmethod
    async def next_control_version(*, session: AsyncSession, user_id: UUID, control_id: str) -> int:
        current = await session.scalar(select(func.max(ComplianceControl.version)).where(ComplianceControl.user_id == user_id, ComplianceControl.control_id == control_id))
        return int(current or 0) + 1

    @classmethod
    async def create_control(cls, *, session, user_id, payload):
        row = ComplianceControl(user_id=user_id, version=await cls.next_control_version(session=session,user_id=user_id,control_id=payload.control_id), **payload.model_dump())
        session.add(row); await session.commit(); await session.refresh(row); return row

    @staticmethod
    async def latest_control(*, session, user_id, control_id):
        return await session.scalar(select(ComplianceControl).where(ComplianceControl.user_id==user_id, ComplianceControl.control_id==control_id, ComplianceControl.active.is_(True)).order_by(ComplianceControl.version.desc()))

    @staticmethod
    async def create_evidence(*, session, user_id, payload):
        collected_at = payload.collected_at or datetime.now(timezone.utc)
        content_hash = payload.content_hash or sha256_payload(payload.payload)
        status = "expired" if payload.expires_at and payload.expires_at <= datetime.now(timezone.utc) else "complete"
        row = ComplianceEvidence(user_id=user_id, control_id=payload.control_id, evidence_type=payload.evidence_type, source=payload.source, subject=payload.subject, payload=payload.payload, evidence_metadata=payload.metadata, status=status, content_hash=content_hash, collected_at=collected_at, expires_at=payload.expires_at)
        session.add(row); await session.commit(); await session.refresh(row); return row

    @staticmethod
    async def get_evidence(*, session, user_id, evidence_ids):
        if not evidence_ids: return []
        return list((await session.scalars(select(ComplianceEvidence).where(ComplianceEvidence.user_id==user_id, ComplianceEvidence.id.in_(evidence_ids)))).all())

    @staticmethod
    async def save_evidence(*, session, row):
        await session.commit(); await session.refresh(row); return row

    @staticmethod
    async def create_record(*, session, user_id, control_id, assessment_status, approval_status, assessment, evidence_snapshot):
        row = ComplianceRecord(user_id=user_id, control_id=control_id, assessment_status=assessment_status, approval_status=approval_status, assessment=assessment, evidence_snapshot=evidence_snapshot)
        session.add(row); await session.commit(); await session.refresh(row); return row

    @staticmethod
    async def get_record(*, session, user_id, record_id):
        return await session.scalar(select(ComplianceRecord).where(ComplianceRecord.user_id==user_id, ComplianceRecord.id==record_id))

    @staticmethod
    async def save_record(*, session, row):
        await session.commit(); await session.refresh(row); return row

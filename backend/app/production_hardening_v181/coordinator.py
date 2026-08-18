from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.production_hardening_v181.repository import ProductionHardeningRepository
from app.production_hardening_v181.schemas import HardeningRunCreate
from app.production_hardening_v181.validation import validate_release_evidence

class HardeningRunNotFoundError(LookupError):
    pass

class ProductionHardeningCoordinator:
    async def create(self, *, session: AsyncSession, user_id: UUID, payload: HardeningRunCreate):
        return await ProductionHardeningRepository.create(
            session=session,
            user_id=user_id,
            release_candidate=payload.release_candidate,
            metadata=payload.metadata,
        )

    async def finalize(self, *, session: AsyncSession, user_id: UUID, run_id: UUID, evidence: dict):
        row = await ProductionHardeningRepository.get(session=session, user_id=user_id, run_id=run_id)
        if row is None:
            raise HardeningRunNotFoundError(f"Hardening run '{run_id}' was not found.")

        report = validate_release_evidence(evidence, release_candidate=row.release_candidate)
        row.report = report.model_dump(mode="json")
        row.status = "passed" if report.overall_status == "PASS" else "failed"
        return await ProductionHardeningRepository.save(session=session, row=row)

production_hardening_coordinator = ProductionHardeningCoordinator()

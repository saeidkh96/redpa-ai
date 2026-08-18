from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.dependencies import CurrentUser, DatabaseSession
from app.production_hardening_v181.coordinator import (
    HardeningRunNotFoundError,
    ProductionHardeningCoordinator,
)
from app.production_hardening_v181.schemas import HardeningRunCreate, HardeningRunResponse

router = APIRouter(prefix="/production-hardening/v18.1", tags=["V18.1 Production Hardening"])
coordinator = ProductionHardeningCoordinator()

@router.post("/runs", response_model=HardeningRunResponse)
async def create_run(payload: HardeningRunCreate, current_user: CurrentUser, session: DatabaseSession):
    row = await coordinator.create(session=session, user_id=current_user.id, payload=payload)
    return HardeningRunResponse(
        id=row.id,
        release_candidate=row.release_candidate,
        status=row.status,
        report=row.report,
        metadata=row.run_metadata,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

@router.post("/runs/{run_id}/finalize", response_model=HardeningRunResponse)
async def finalize_run(run_id: UUID, evidence: dict, current_user: CurrentUser, session: DatabaseSession):
    try:
        row = await coordinator.finalize(
            session=session,
            user_id=current_user.id,
            run_id=run_id,
            evidence=evidence,
        )
    except HardeningRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return HardeningRunResponse(
        id=row.id,
        release_candidate=row.release_candidate,
        status=row.status,
        report=row.report,
        metadata=row.run_metadata,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

from __future__ import annotations

from fastapi import APIRouter

from app.performance.service import (
    PerformanceStatusService,
)


router = APIRouter(
    prefix="/performance",
    tags=["Performance"],
)


@router.get("/snapshot")
async def performance_snapshot() -> dict:
    return await (
        PerformanceStatusService.snapshot()
    )

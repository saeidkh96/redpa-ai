from __future__ import annotations

from fastapi import (
    APIRouter,
    Response,
    status,
)

from app.health.schemas import (
    HealthResponse,
)
from app.health.service import (
    HealthService,
)


router = APIRouter(
    prefix="/platform",
    tags=["Platform Health"],
)


@router.get(
    "/live",
    response_model=HealthResponse,
)
async def liveness() -> HealthResponse:
    return await HealthService.liveness()


@router.get(
    "/ready",
    response_model=HealthResponse,
)
async def readiness(
    response: Response,
) -> HealthResponse:
    result = await HealthService.readiness()

    if result.status != "ready":
        response.status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return result


@router.get(
    "/health",
    response_model=HealthResponse,
)
async def deep_health(
    response: Response,
) -> HealthResponse:
    result = await HealthService.deep_health()

    if result.status != "healthy":
        response.status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return result

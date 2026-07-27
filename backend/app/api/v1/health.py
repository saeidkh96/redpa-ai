import logging
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import settings


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str
    version: str
    environment: str
    request_id: str


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check API health",
)
async def health_check(request: Request) -> HealthResponse:
    """Return the current API health status."""

    logger.info("Health check requested")

    return HealthResponse(
        status="healthy",
        service=f"{settings.app_name} API",
        version=settings.app_version,
        environment=settings.environment,
        request_id=request.state.request_id,
    )
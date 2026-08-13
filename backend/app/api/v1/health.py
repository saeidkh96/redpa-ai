from fastapi import APIRouter, status

from app.core.config import settings
from app.database.session import check_database_connection
from app.schemas.health import HealthResponse, ServiceStatus


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check application health",
)
async def get_health() -> HealthResponse:
    """
    Return application and database health information.
    """

    database_is_healthy = await check_database_connection()

    return HealthResponse(
        status="healthy" if database_is_healthy else "degraded",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        database=ServiceStatus(
            status="healthy" if database_is_healthy else "unhealthy",
        ),
    )
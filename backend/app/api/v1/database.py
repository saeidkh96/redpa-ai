from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.database.health import check_database_connection
from app.database.session import engine


router = APIRouter(
    prefix="/database",
    tags=["Database"],
)


class DatabaseHealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"]
    database: str


@router.get(
    "/health",
    response_model=DatabaseHealthResponse,
    summary="Check database health",
)
async def database_health() -> DatabaseHealthResponse:
    """
    Verify that the application can connect to PostgreSQL.
    """

    is_healthy = await check_database_connection(engine)

    return DatabaseHealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        database="postgresql",
    )
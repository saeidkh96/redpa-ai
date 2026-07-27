from fastapi import APIRouter

from app.api.v1.debug import router as debug_router
from app.api.v1.health import router as health_router
from app.core.config import settings


api_router = APIRouter()

api_router.include_router(health_router)

if settings.environment == "development":
    api_router.include_router(debug_router)
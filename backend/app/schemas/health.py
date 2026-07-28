from typing import Literal

from pydantic import BaseModel


class ServiceStatus(BaseModel):
    status: Literal["healthy", "unhealthy"]


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"]
    service: str
    version: str
    environment: str
    database: ServiceStatus
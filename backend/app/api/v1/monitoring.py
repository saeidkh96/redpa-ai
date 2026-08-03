from fastapi import APIRouter
from starlette.responses import Response

from app.monitoring.metrics import (
    prometheus_metrics_endpoint,
)


router = APIRouter(
    tags=["Monitoring"],
    include_in_schema=False,
)


@router.get(
    "/metrics",
    response_class=Response,
    summary="Prometheus metrics",
)
async def get_prometheus_metrics() -> Response:
    return await prometheus_metrics_endpoint()

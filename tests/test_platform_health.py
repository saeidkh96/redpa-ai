import pytest

from app.health.service import (
    HealthService,
)


@pytest.mark.asyncio
async def test_liveness_is_healthy() -> None:
    result = await HealthService.liveness()

    assert result.status == "healthy"
    assert result.dependencies == []

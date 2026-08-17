import pytest

from app.production_validation.detector import FailureDetector
from app.production_validation.schemas import HealthProbeResult
from app.production_validation.service import ProductionValidationService


@pytest.mark.asyncio
async def test_repeated_failure_creates_incident_signal() -> None:
    service = ProductionValidationService(
        detector=FailureDetector(threshold=3, cooldown_seconds=0)
    )
    created = []

    async def create_incident(result: HealthProbeResult):
        incident = {"service": result.service, "source": "production-validation"}
        created.append(incident)
        return incident

    failed = HealthProbeResult(
        service="redpa-research-agent",
        healthy=False,
        status="unhealthy",
    )

    assert await service.evaluate_probe(result=failed, create_incident=create_incident) is None
    assert await service.evaluate_probe(result=failed, create_incident=create_incident) is None
    incident = await service.evaluate_probe(result=failed, create_incident=create_incident)

    assert incident is not None
    assert len(created) == 1
    assert created[0]["source"] == "production-validation"

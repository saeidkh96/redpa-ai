from __future__ import annotations

from typing import Awaitable, Callable

from app.production_validation.detector import FailureDetector
from app.production_validation.schemas import HealthProbeResult

IncidentCreator = Callable[[HealthProbeResult], Awaitable[object]]


class ProductionValidationService:
    """Turns repeated service-health failures into deduplicated incident signals."""

    def __init__(self, *, detector: FailureDetector | None = None) -> None:
        self.detector = detector or FailureDetector()

    async def evaluate_probe(
        self,
        *,
        result: HealthProbeResult,
        create_incident: IncidentCreator,
    ) -> object | None:
        if not self.detector.observe(result):
            return None
        return await create_incident(result)


production_validation_service = ProductionValidationService()

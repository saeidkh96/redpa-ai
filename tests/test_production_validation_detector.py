from app.production_validation.detector import FailureDetector
from app.production_validation.schemas import HealthProbeResult


def probe(healthy: bool) -> HealthProbeResult:
    return HealthProbeResult(
        service="redpa-research-agent",
        healthy=healthy,
        status="healthy" if healthy else "unhealthy",
    )


def test_detector_requires_three_consecutive_failures() -> None:
    detector = FailureDetector(threshold=3, cooldown_seconds=0)
    assert detector.observe(probe(False)) is False
    assert detector.observe(probe(False)) is False
    assert detector.observe(probe(False)) is True


def test_success_resets_failure_counter() -> None:
    detector = FailureDetector(threshold=3, cooldown_seconds=0)
    detector.observe(probe(False))
    detector.observe(probe(False))
    assert detector.observe(probe(True)) is False
    assert detector.failure_count("redpa-research-agent") == 0
    assert detector.observe(probe(False)) is False

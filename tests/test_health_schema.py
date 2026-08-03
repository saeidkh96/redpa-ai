from app.health.schemas import (
    DependencyHealth,
)


def test_dependency_health_defaults() -> None:
    result = DependencyHealth(
        name="redis",
        status="healthy",
    )

    assert result.metadata == {}
    assert result.latency_ms is None

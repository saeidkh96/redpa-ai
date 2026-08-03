from app.agent_memory.analytics import (
    AgentMemoryAnalyticsService,
)


def test_analytics_service_exists() -> None:
    assert hasattr(
        AgentMemoryAnalyticsService,
        "overview",
    )

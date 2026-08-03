import json

import pytest

from app.a2a_protocol.coordinator import RedPACoordinatorAgent


@pytest.mark.asyncio
async def test_coordinator_returns_health() -> None:
    result = await RedPACoordinatorAgent().invoke(
        "Show available agents and health"
    )

    payload = json.loads(result)

    assert payload["total_agents"] >= 5


@pytest.mark.asyncio
async def test_coordinator_discovers_research() -> None:
    result = await RedPACoordinatorAgent().invoke(
        "Find an agent for web research and evidence"
    )

    payload = json.loads(result)

    assert any(
        match["agent_id"] == "research"
        for match in payload["matches"]
    )

import pytest

from app.a2a.registry import (
    AgentAlreadyRegisteredError,
    AgentRegistry,
)
from app.a2a.schemas import (
    AgentCapability,
    AgentCard,
    AgentStatus,
)
from datetime import datetime, timezone


def make_card(
    agent_id: str = "test-agent",
) -> AgentCard:
    now = datetime.now(
        timezone.utc,
    )

    return AgentCard(
        id=agent_id,
        name="Test Agent",
        version="1.0.0",
        description="Test agent.",
        status=AgentStatus.ACTIVE,
        capabilities=[
            AgentCapability(
                name="test_capability",
                description="Performs testing.",
                tags=["test"],
            )
        ],
        registered_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_register_and_get_agent() -> None:
    registry = AgentRegistry()
    card = make_card()

    await registry.register(
        card,
    )

    result = await registry.get(
        card.id,
    )

    assert result.id == card.id


@pytest.mark.asyncio
async def test_duplicate_registration_is_rejected() -> None:
    registry = AgentRegistry()
    card = make_card()

    await registry.register(
        card,
    )

    with pytest.raises(
        AgentAlreadyRegisteredError,
    ):
        await registry.register(
            card,
        )


@pytest.mark.asyncio
async def test_capability_discovery() -> None:
    registry = AgentRegistry()
    await registry.register(
        make_card(),
    )

    result = await registry.discover(
        "testing capability",
    )

    assert result.total == 1
    assert result.matches[0].agent_id == "test-agent"

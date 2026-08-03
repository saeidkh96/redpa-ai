import pytest

from app.a2a_remote.registry import (
    RemoteAgentAlreadyRegisteredError,
    RemoteAgentRecord,
    RemoteAgentRegistry,
)


@pytest.mark.asyncio
async def test_register_remote_agent() -> None:
    registry = RemoteAgentRegistry()

    record = RemoteAgentRecord(
        name="coordinator",
        base_url="http://localhost:8050",
        enabled=True,
        timeout_seconds=30.0,
    )

    await registry.register(
        record,
    )

    result = await registry.get(
        "coordinator",
    )

    assert result.base_url == (
        "http://localhost:8050"
    )


@pytest.mark.asyncio
async def test_duplicate_remote_agent_is_rejected() -> None:
    registry = RemoteAgentRegistry()

    record = RemoteAgentRecord(
        name="coordinator",
        base_url="http://localhost:8050",
        enabled=True,
        timeout_seconds=30.0,
    )

    await registry.register(
        record,
    )

    with pytest.raises(
        RemoteAgentAlreadyRegisteredError,
    ):
        await registry.register(
            record,
        )

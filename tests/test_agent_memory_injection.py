import pytest

from app.agent_memory.injection import (
    AgentMemoryInjectionService,
)


@pytest.mark.asyncio
async def test_injection_without_memory(
    monkeypatch,
) -> None:
    async def fake_build(**kwargs):
        return ""

    monkeypatch.setattr(
        (
            "app.agent_memory.injection."
            "AgentMemoryContextBuilder.build"
        ),
        fake_build,
    )

    result = await AgentMemoryInjectionService.inject(
        prompt="Hello",
        agent_id="planner",
    )

    assert result.used_memory is False
    assert result.injected_prompt == "Hello"

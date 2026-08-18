from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.a2a.registry import agent_registry
from app.a2a.schemas import (
    AgentCapability,
    AgentCard,
    AgentEndpoint,
    AgentStatus,
)
from app.a2a.service import AgentService
from app.a2a_remote.client import RemoteA2AError
from app.self_healing.executor import (
    ReplacementExecutionAdapter,
)


def _replacement_card() -> AgentCard:
    now = datetime.now(
        timezone.utc
    )

    return AgentCard(
        id="research-fallback",
        name="Research Fallback",
        version="1.0.0",
        description=(
            "V12 replacement research agent."
        ),
        status=AgentStatus.ACTIVE,
        capabilities=[
            AgentCapability(
                name="research",
                description=(
                    "Research and evidence collection"
                ),
                tags=[
                    "research",
                    "search",
                ],
                input_modes=["text"],
                output_modes=["text"],
                examples=[
                    "Research an AI topic"
                ],
            )
        ],
        supported_routes=[],
        endpoint=AgentEndpoint(
            url="http://research-fallback:8061",
            transport="internal",
        ),
        metadata={
            "timeout_seconds": "30"
        },
        registered_at=now,
        updated_at=now,
    )


@pytest.fixture(autouse=True)
def isolate_registry():
    original_agents = dict(
        agent_registry._agents
    )
    original_initialized = (
        AgentService._initialized
    )

    agent_registry._agents.clear()
    AgentService._initialized = True

    try:
        yield
    finally:
        agent_registry._agents.clear()
        agent_registry._agents.update(
            original_agents
        )
        AgentService._initialized = (
            original_initialized
        )


@pytest.mark.asyncio
async def test_stage6_executes_through_existing_remote_a2a_client():
    await agent_registry.register(
        _replacement_card()
    )

    remote_response = SimpleNamespace(
        success=True,
        event_count=2,
        events=[
            {
                "type": "task",
                "state": "working",
            },
            {
                "type": "task",
                "state": "completed",
            },
        ],
        final_response={
            "type": "task",
            "state": "completed",
        },
        execution_time_ms=42.5,
        error=None,
    )

    delegate_mock = AsyncMock(
        return_value=remote_response
    )

    adapter = ReplacementExecutionAdapter()

    with patch(
        "app.self_healing.executor."
        "RemoteA2AClient.delegate",
        new=delegate_mock,
    ):
        result = await adapter.execute(
            {
                "source_agent_id": (
                    "research-primary"
                ),
                "target_agent_id": (
                    "research-fallback"
                ),
                "task": (
                    "Continue the research task"
                ),
                "workflow_id": "wf-v12",
                "run_id": "run-v12",
                "trace_id": "trace-v12",
                "context": {
                    "messages": ["one"]
                },
            }
        )

    assert result["accepted"] is True
    assert (
        result["agent_id"]
        == "research-fallback"
    )
    assert result["event_count"] == 2

    assert result["final_response"] == {
        "type": "task",
        "state": "completed",
    }

    delegate_mock.assert_awaited_once()

    record = (
        delegate_mock.await_args.args[0]
    )

    assert record.name == "research-fallback"
    assert (
        record.base_url
        == "http://research-fallback:8061"
    )

    assert (
        delegate_mock.await_args.kwargs[
            "timeout_seconds"
        ]
        == 30.0
    )


@pytest.mark.asyncio
async def test_stage6_verification_requires_real_a2a_evidence():
    adapter = (
        ReplacementExecutionAdapter()
    )

    verification = await adapter.verify(
        target_agent_id=(
            "research-fallback"
        ),
        execution_result={
            "accepted": True,
            "event_count": 2,
            "final_response": {
                "state": "completed"
            },
            "execution_time_ms": 15.0,
            "remote_error": None,
        },
    )

    assert verification["healthy"] is True
    assert verification["accepted"] is True
    assert verification["event_count"] == 2
    assert (
        verification[
            "final_response_present"
        ]
        is True
    )


@pytest.mark.asyncio
async def test_stage6_empty_event_stream_fails_verification():
    adapter = (
        ReplacementExecutionAdapter()
    )

    verification = await adapter.verify(
        target_agent_id=(
            "research-fallback"
        ),
        execution_result={
            "accepted": False,
            "event_count": 0,
            "final_response": None,
            "execution_time_ms": 4.0,
            "remote_error": None,
        },
    )

    assert verification["healthy"] is False


@pytest.mark.asyncio
async def test_stage6_missing_agent_endpoint_fails_closed():
    card = _replacement_card()

    card_without_endpoint = (
        card.model_copy(
            update={
                "endpoint": None,
            }
        )
    )

    await agent_registry.register(
        card_without_endpoint
    )

    adapter = ReplacementExecutionAdapter()

    with pytest.raises(
        RuntimeError,
        match="does not expose an A2A endpoint",
    ):
        await adapter.execute(
            {
                "target_agent_id": (
                    "research-fallback"
                ),
                "task": "Continue research",
            }
        )


@pytest.mark.asyncio
async def test_stage6_remote_a2a_failure_propagates():
    await agent_registry.register(
        _replacement_card()
    )

    adapter = ReplacementExecutionAdapter()

    with patch(
        "app.self_healing.executor."
        "RemoteA2AClient.delegate",
        new=AsyncMock(
            side_effect=RemoteA2AError(
                "Remote A2A delegation failed"
            )
        ),
    ):
        with pytest.raises(
            RemoteA2AError
        ):
            await adapter.execute(
                {
                    "target_agent_id": (
                        "research-fallback"
                    ),
                    "task": (
                        "Continue research"
                    ),
                }
            )
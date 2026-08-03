from app.agent_memory.schemas import (
    SharedMemoryPublishRequest,
)


def test_shared_memory_visibility_defaults_to_all() -> None:
    payload = SharedMemoryPublishRequest(
        source_agent_id="research-agent",
        content="Research completed successfully.",
    )

    assert payload.visible_to_agents == []
    assert payload.importance == 0.5

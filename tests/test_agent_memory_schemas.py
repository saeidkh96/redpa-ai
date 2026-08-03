from app.agent_memory.schemas import (
    MemoryCreate,
    MemorySearchRequest,
)


def test_memory_create_defaults() -> None:
    payload = MemoryCreate(
        agent_id="planner",
        content="User prefers concise answers.",
    )

    assert payload.scope == "private"
    assert payload.kind == "observation"
    assert payload.embed is True


def test_memory_search_defaults() -> None:
    payload = MemorySearchRequest(
        query="user preferences",
    )

    assert payload.limit == 8
    assert payload.include_shared is True

from app.agent_memory.semantic import (
    MemorySemanticStore,
)


def test_embedding_has_expected_size() -> None:
    vector = MemorySemanticStore.embed_text(
        "RedPA durable distributed workflow memory"
    )

    assert len(
        vector,
    ) == MemorySemanticStore.VECTOR_SIZE


def test_embedding_is_deterministic() -> None:
    first = MemorySemanticStore.embed_text(
        "shared agent memory"
    )

    second = MemorySemanticStore.embed_text(
        "shared agent memory"
    )

    assert first == second


def test_embedding_is_normalized() -> None:
    vector = MemorySemanticStore.embed_text(
        "semantic memory retrieval"
    )

    norm = sum(
        value * value
        for value in vector
    ) ** 0.5

    assert round(
        norm,
        6,
    ) == 1.0

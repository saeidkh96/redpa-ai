from app.agent_memory.maintenance import (
    AgentMemoryMaintenanceService,
)


def test_token_similarity_identical() -> None:
    score = (
        AgentMemoryMaintenanceService
        ._token_similarity(
            "User prefers concise technical answers.",
            "User prefers concise technical answers.",
        )
    )

    assert score == 1.0


def test_token_similarity_partial() -> None:
    score = (
        AgentMemoryMaintenanceService
        ._token_similarity(
            "User prefers concise answers.",
            "User prefers detailed answers.",
        )
    )

    assert 0.0 < score < 1.0


def test_fingerprint_is_deterministic() -> None:
    first = AgentMemoryMaintenanceService._fingerprint(
        "Agent memory result"
    )

    second = AgentMemoryMaintenanceService._fingerprint(
        "Agent   memory result"
    )

    assert first == second

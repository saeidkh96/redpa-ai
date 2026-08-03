import pytest

from app.a2a.builtin_agents import (
    build_builtin_agent_cards,
)
from app.a2a.service import AgentService


def test_builtin_agent_ids_are_unique() -> None:
    cards = build_builtin_agent_cards()
    ids = [
        card.id
        for card in cards
    ]

    assert len(ids) == len(
        set(
            ids,
        )
    )


@pytest.mark.asyncio
async def test_builtin_agents_are_registered() -> None:
    result = await AgentService.list_agents()

    assert result.total >= 5

    ids = {
        item.id
        for item in result.items
    }

    assert {
        "planner",
        "research",
        "rag",
        "tool",
        "reviewer",
    }.issubset(
        ids,
    )

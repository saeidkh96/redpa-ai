from app.research_agent.card import (
    build_research_agent_card,
)


def test_research_agent_card() -> None:
    card = build_research_agent_card()

    assert card.name == "RedPA Research Agent"
    assert card.version == "0.6.0"
    assert len(card.skills) == 1
    assert card.skills[0].id == "web_research"

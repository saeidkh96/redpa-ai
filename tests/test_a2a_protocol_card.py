import pytest

pytest.importorskip("a2a")

from app.a2a_protocol.card import build_public_agent_card


def test_public_agent_card_uses_a2a_v1() -> None:
    card = build_public_agent_card()

    assert card.name == "RedPA Coordinator Agent"
    assert card.supported_interfaces
    assert (
        card.supported_interfaces[0].protocol_version
        == "1.0"
    )
    assert len(card.skills) == 2

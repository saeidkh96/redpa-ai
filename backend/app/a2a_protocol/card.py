from __future__ import annotations

import os

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)


def build_public_agent_card() -> AgentCard:
    public_url = os.getenv(
        "A2A_PUBLIC_URL",
        "http://localhost:8050",
    ).rstrip("/")

    return AgentCard(
        name="RedPA Coordinator Agent",
        description=(
            "A public A2A coordinator for discovering RedPA agents, "
            "capabilities, and platform health."
        ),
        version="0.5.0",
        default_input_modes=["text/plain"],
        default_output_modes=[
            "application/json",
            "text/plain",
        ],
        capabilities=AgentCapabilities(
            streaming=False,
            extended_agent_card=False,
        ),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                url=public_url,
                protocol_version="1.0",
            )
        ],
        skills=[
            AgentSkill(
                id="redpa_agent_discovery",
                name="RedPA Agent Discovery",
                description=(
                    "Discover the most appropriate active RedPA agent and "
                    "capability for a requested task."
                ),
                input_modes=["text/plain"],
                output_modes=[
                    "application/json",
                    "text/plain",
                ],
                tags=[
                    "a2a",
                    "discovery",
                    "routing",
                    "capabilities",
                    "redpa",
                ],
                examples=[
                    "Find an agent for web research.",
                    "Which agent can inspect Docker containers?",
                ],
            ),
            AgentSkill(
                id="redpa_agent_health",
                name="RedPA Agent Health",
                description=(
                    "Return health and availability information for "
                    "registered RedPA agents."
                ),
                input_modes=["text/plain"],
                output_modes=[
                    "application/json",
                    "text/plain",
                ],
                tags=[
                    "a2a",
                    "health",
                    "agents",
                    "availability",
                    "redpa",
                ],
                examples=[
                    "Show agent registry health.",
                    "List available agents.",
                ],
            ),
        ],
    )

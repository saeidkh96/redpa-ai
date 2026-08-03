from __future__ import annotations

import os

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)


def build_research_agent_card() -> AgentCard:
    public_url = os.getenv(
        "RESEARCH_AGENT_PUBLIC_URL",
        "http://research-agent:8061",
    ).rstrip("/")

    return AgentCard(
        name="RedPA Research Agent",
        description=(
            "A remote RedPA specialist for public web research, "
            "evidence collection, deduplication, and ranking."
        ),
        supported_interfaces=[
            AgentInterface(
                url=public_url,
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
        version="0.6.0",
        capabilities=AgentCapabilities(
            streaming=False,
            extended_agent_card=False,
        ),
        default_input_modes=[
            "text/plain",
        ],
        default_output_modes=[
            "application/json",
            "text/plain",
        ],
        skills=[
            AgentSkill(
                id="web_research",
                name="Web Research",
                description=(
                    "Search the public web and return ranked evidence "
                    "for a research query."
                ),
                tags=[
                    "research",
                    "web",
                    "evidence",
                    "sources",
                    "ranking",
                ],
                examples=[
                    "Research recent developments in agentic AI.",
                    "Find current evidence about LangGraph durable execution.",
                ],
                input_modes=[
                    "text/plain",
                ],
                output_modes=[
                    "application/json",
                    "text/plain",
                ],
            )
        ],
    )

from __future__ import annotations

from datetime import datetime, timezone

from app.a2a.registry import agent_registry
from app.a2a.schemas import (
    AgentCapability,
    AgentCard,
    AgentEndpoint,
    AgentStatus,
)


def _now():
    return datetime.now(
        timezone.utc,
    )


def build_builtin_agent_cards() -> list[AgentCard]:
    now = _now()

    return [
        AgentCard(
            id="planner",
            name="Planner Agent",
            version="1.0.0",
            description=(
                "Selects the safest and most appropriate RedPA workflow "
                "route for a user request."
            ),
            status=AgentStatus.ACTIVE,
            capabilities=[
                AgentCapability(
                    name="route_selection",
                    description=(
                        "Select chat, research, RAG, tool, or human-review "
                        "execution routes."
                    ),
                    tags=[
                        "planning",
                        "routing",
                        "orchestration",
                    ],
                    examples=[
                        "Choose the best workflow for this request.",
                    ],
                )
            ],
            supported_routes=[
                "chat",
                "research",
                "rag",
                "tool",
                "human_review",
            ],
            endpoint=AgentEndpoint(
                url="internal://planner",
            ),
            metadata={
                "framework": "langgraph",
                "visibility": "internal",
            },
            registered_at=now,
            updated_at=now,
        ),
        AgentCard(
            id="research",
            name="Research Agent",
            version="1.0.0",
            description=(
                "Collects, ranks, and synthesizes current web evidence."
            ),
            status=AgentStatus.ACTIVE,
            capabilities=[
                AgentCapability(
                    name="web_research",
                    description=(
                        "Search the public web and synthesize ranked evidence."
                    ),
                    tags=[
                        "research",
                        "web",
                        "sources",
                        "evidence",
                    ],
                    examples=[
                        "Research LangGraph durable execution.",
                    ],
                )
            ],
            supported_routes=[
                "research",
            ],
            endpoint=AgentEndpoint(
                url="internal://research",
            ),
            metadata={
                "framework": "langgraph",
                "visibility": "internal",
            },
            registered_at=now,
            updated_at=now,
        ),
        AgentCard(
            id="rag",
            name="RAG Agent",
            version="1.0.0",
            description=(
                "Retrieves relevant document chunks and produces "
                "source-grounded responses."
            ),
            status=AgentStatus.ACTIVE,
            capabilities=[
                AgentCapability(
                    name="document_retrieval",
                    description=(
                        "Retrieve and synthesize knowledge from indexed "
                        "documents."
                    ),
                    tags=[
                        "rag",
                        "documents",
                        "retrieval",
                        "qdrant",
                    ],
                    examples=[
                        "Answer this question using uploaded documents.",
                    ],
                )
            ],
            supported_routes=[
                "rag",
            ],
            endpoint=AgentEndpoint(
                url="internal://rag",
            ),
            metadata={
                "framework": "langgraph",
                "visibility": "internal",
            },
            registered_at=now,
            updated_at=now,
        ),
        AgentCard(
            id="tool",
            name="Tool Agent",
            version="1.0.0",
            description=(
                "Executes internal tools and MCP tools through the unified "
                "tool runtime."
            ),
            status=AgentStatus.ACTIVE,
            capabilities=[
                AgentCapability(
                    name="tool_execution",
                    description=(
                        "Execute validated internal and MCP tools."
                    ),
                    tags=[
                        "tools",
                        "mcp",
                        "filesystem",
                        "github",
                        "postgres",
                        "docker",
                    ],
                    examples=[
                        "Show Docker containers.",
                        "List GitHub commits.",
                    ],
                )
            ],
            supported_routes=[
                "tool",
            ],
            endpoint=AgentEndpoint(
                url="internal://tool",
            ),
            metadata={
                "framework": "langgraph",
                "visibility": "internal",
            },
            registered_at=now,
            updated_at=now,
        ),
        AgentCard(
            id="reviewer",
            name="Human Review Agent",
            version="1.0.0",
            description=(
                "Coordinates persisted approval, rejection, and workflow "
                "resume boundaries."
            ),
            status=AgentStatus.ACTIVE,
            capabilities=[
                AgentCapability(
                    name="approval_coordination",
                    description=(
                        "Pause sensitive workflows and resume them after an "
                        "authorized human decision."
                    ),
                    tags=[
                        "approval",
                        "review",
                        "human",
                        "safety",
                    ],
                    examples=[
                        "Request approval before a sensitive action.",
                    ],
                )
            ],
            supported_routes=[
                "human_review",
            ],
            endpoint=AgentEndpoint(
                url="internal://reviewer",
            ),
            metadata={
                "framework": "langgraph",
                "visibility": "internal",
            },
            registered_at=now,
            updated_at=now,
        ),
    ]


async def register_builtin_agents() -> None:
    for card in build_builtin_agent_cards():
        await agent_registry.register(
            card,
            replace=True,
        )

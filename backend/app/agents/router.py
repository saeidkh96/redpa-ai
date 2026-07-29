from typing import Literal

from app.agents.state import AgentState


GraphDestination = Literal[
    "chat",
    "rag",
    "capability_unavailable",
]


def route_after_planner(
    state: AgentState,
) -> GraphDestination:
    route = state.get("route")

    if route == "chat":
        return "chat"

    if route == "rag":
        return "rag"

    return "capability_unavailable"
from __future__ import annotations

from typing import Any, Literal

from app.agents.state import AgentRoute, AgentState


GraphDestination = Literal[
    "chat",
    "rag",
    "research",
    "tool",
    "human_review",
    "capability_unavailable",
]


SUPPORTED_ROUTE_DESTINATIONS: dict[
    AgentRoute,
    GraphDestination,
] = {
    "chat": "chat",
    "rag": "rag",
    "research": "research",
    "tool": "tool",
    "sql": "capability_unavailable",
    "human_review": "human_review",
}


def route_after_planner(
    state: AgentState,
) -> GraphDestination:
    """
    Select the next graph node after the planner has completed.

    During a normal workflow, the planner route is used directly.

    During a resumed workflow, an approved request must never be
    sent back to the human-review node. Instead, the router attempts
    to recover the approved execution route from the stored action
    payload or requested action.
    """

    approval_granted = bool(
        state.get(
            "approval_granted",
            False,
        )
    )

    approved_review_id = _optional_string(
        state.get(
            "approved_review_id",
        )
    )

    if approval_granted and approved_review_id:
        return _route_approved_workflow(
            state,
        )

    route = _normalize_agent_route(
        state.get(
            "route",
        )
    )

    if route is None:
        return "capability_unavailable"

    return SUPPORTED_ROUTE_DESTINATIONS.get(
        route,
        "capability_unavailable",
    )


def _route_approved_workflow(
    state: AgentState,
) -> GraphDestination:
    """
    Determine where an approved workflow should continue.

    Priority:

    1. action_payload["resume_route"]
    2. action_payload["original_route"]
    3. action_payload["route"]
    4. requested_action
    5. current state route

    The human-review route is explicitly rejected during resume so
    that approval cannot create an infinite human-review loop.
    """

    action_payload = state.get(
        "action_payload",
    )

    if not isinstance(
        action_payload,
        dict,
    ):
        action_payload = {}

    route_candidates: tuple[Any, ...] = (
        action_payload.get(
            "resume_route",
        ),
        action_payload.get(
            "original_route",
        ),
        action_payload.get(
            "route",
        ),
        state.get(
            "requested_action",
        ),
        state.get(
            "route",
        ),
    )

    for candidate in route_candidates:
        route = _normalize_agent_route(
            candidate,
        )

        if route is None:
            continue

        if route == "human_review":
            continue

        return SUPPORTED_ROUTE_DESTINATIONS.get(
            route,
            "capability_unavailable",
        )

    return "capability_unavailable"


def _normalize_agent_route(
    value: Any,
) -> AgentRoute | None:
    if value is None:
        return None

    normalized_value = str(
        value,
    ).strip().casefold()

    aliases: dict[str, AgentRoute] = {
        "chat": "chat",
        "conversation": "chat",
        "general_chat": "chat",
        "rag": "rag",
        "retrieval": "rag",
        "document_search": "rag",
        "knowledge_base": "rag",
        "research": "research",
        "web_research": "research",
        "web_search": "research",
        "tool": "tool",
        "tool_execution": "tool",
        "execute_tool": "tool",
        "calculator": "tool",
        "calculate": "tool",
        "sql": "sql",
        "database": "sql",
        "database_query": "sql",
        "human_review": "human_review",
        "review": "human_review",
        "manual_approval": "human_review",
    }

    return aliases.get(
        normalized_value,
    )


def _optional_string(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized_value = str(
        value,
    ).strip()

    if not normalized_value:
        return None

    return normalized_value
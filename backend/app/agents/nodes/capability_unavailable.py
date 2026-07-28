from app.agents.state import AgentState
from app.core.exceptions import LLMInvalidResponseError


CAPABILITY_MESSAGES: dict[str, str] = {
    "rag": (
        "The request was routed to the document retrieval "
        "workflow, but the RAG capability has not been enabled yet."
    ),
    "sql": (
        "The request was routed to the database workflow, "
        "but the SQL agent has not been enabled yet."
    ),
    "tool": (
        "The request was routed to the tool workflow, "
        "but external tool execution has not been enabled yet."
    ),
    "research": (
        "The request was routed to the research workflow, "
        "but external research has not been enabled yet."
    ),
    "human_review": (
        "The request was routed to the human review workflow, "
        "but the approval queue has not been enabled yet."
    ),
}


async def capability_unavailable_node(
    state: AgentState,
) -> dict[str, object]:
    route = state.get("route")

    if not isinstance(route, str):
        raise LLMInvalidResponseError(
            "The planner did not provide a valid workflow route."
        )

    response_content = CAPABILITY_MESSAGES.get(
        route,
    )

    if response_content is None:
        raise LLMInvalidResponseError(
            f"The workflow route '{route}' is not supported."
        )

    return {
        "response_content": response_content,
        "model": "redpa-router",
        "provider": "internal",
        "usage": {},
    }
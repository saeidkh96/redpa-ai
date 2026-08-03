from __future__ import annotations

from app.agents.state import AgentState
from app.services.a2a_chat_service import A2AChatService


async def a2a_node(
    state: AgentState,
) -> dict[str, object]:
    latest_user_message = _get_latest_user_message(
        state,
    )

    if latest_user_message is None:
        return {
            "response_content": (
                "The A2A workflow could not find a user request."
            ),
            "model": "a2a-unavailable",
            "provider": "redpa-a2a-runtime",
            "usage": {
                "remote_agent": None,
                "success": False,
            },
            "completed": False,
            "error": "Missing user request.",
        }

    result = await A2AChatService.delegate(
        latest_user_message,
    )

    return {
        "response_content": result[
            "response_content"
        ],
        "model": (
            f"a2a:{result.get('remote_agent') or 'unavailable'}"
        ),
        "provider": "redpa-a2a-runtime",
        "usage": {
            "remote_agent": result.get("remote_agent"),
            "remote_base_url": result.get("base_url"),
            "selected_skill": result.get("selected_skill"),
            "selection_score": result.get(
                "selection_score",
                0.0,
            ),
            "selection_terms": result.get(
                "selection_terms",
                [],
            ),
            "task_id": result.get("task_id"),
            "context_id": result.get("context_id"),
            "event_count": result.get("event_count", 0),
            "execution_time_ms": result.get(
                "execution_time_ms",
                0.0,
            ),
            "success": result.get("success", False),
            "error": result.get("error"),
        },
        "completed": False,
        "error": result.get("error"),
    }


def _get_latest_user_message(
    state: AgentState,
) -> str | None:
    messages = state.get("messages", [])

    if not isinstance(messages, list):
        return None

    for message in reversed(messages):
        if not isinstance(message, dict):
            continue

        if str(
            message.get("role", "")
        ).casefold() != "user":
            continue

        content = str(
            message.get("content", "")
            or ""
        ).strip()

        if content:
            return content

    return None

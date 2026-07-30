from __future__ import annotations

from typing import Any

from app.agents.state import AgentState


def _get_latest_user_message(
    state: AgentState,
) -> str | None:
    messages = state.get(
        "messages",
        [],
    )

    for message in reversed(messages):
        if message.get("role") != "user":
            continue

        content = str(
            message.get(
                "content",
                "",
            )
            or ""
        ).strip()

        if content:
            return content

    return None


async def human_review_node(
    state: AgentState,
) -> dict[str, Any]:
    review_reason = str(
        state.get(
            "review_reason",
            "",
        )
        or state.get(
            "planner_reason",
            "",
        )
        or "The request requires human review."
    ).strip()

    requested_action = str(
        state.get(
            "requested_action",
            "",
        )
        or state.get(
            "route",
            "",
        )
        or "workflow_execution"
    ).strip()

    request_content = state.get(
        "request_content",
    )

    if not request_content:
        request_content = _get_latest_user_message(
            state,
        )

    action_payload = state.get(
        "action_payload",
    )

    if not isinstance(action_payload, dict):
        action_payload = {
            "route": state.get(
                "route",
                "human_review",
            ),
            "planner_reason": state.get(
                "planner_reason",
                review_reason,
            ),
        }

    return {
        "requires_human_review": True,
        "review_status": "pending",
        "review_reason": review_reason,
        "review_id": None,
        "requested_action": requested_action,
        "request_content": request_content,
        "action_payload": action_payload,
        "reviewed_by": None,
        "reviewed_at": None,
        "reviewer_feedback": None,
        "response_content": (
            "This request requires human approval before "
            "the workflow can continue."
        ),
        "model": "system",
        "provider": "redpa",
        "usage": {
            "human_review": True,
            "review_status": "pending",
        },
        "completed": True,
        "error": None,
    }
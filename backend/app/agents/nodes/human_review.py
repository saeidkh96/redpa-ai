from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.agents.state import AgentState


async def human_review_node(
    state: AgentState,
) -> dict[str, Any]:
    review_id = state.get(
        "review_id",
    )

    if not review_id:
        review_id = str(
            uuid.uuid4()
        )

    review_reason = state.get(
        "review_reason",
    )

    if not review_reason:
        review_reason = state.get(
            "planner_reason",
            "The request requires human review.",
        )

    return {
        "requires_human_review": True,
        "review_status": "pending",
        "review_reason": review_reason,
        "review_id": review_id,
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
        },
        "completed": True,
        "error": None,
    }
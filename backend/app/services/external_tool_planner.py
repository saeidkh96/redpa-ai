from __future__ import annotations

from app.schemas.planner import PlannerResult
from app.tools.intent import detect_external_tool_intent


def create_external_tool_plan(
    user_message: str,
) -> PlannerResult | None:
    """
    Return a deterministic tool plan for supported external tools.
    """

    intent = detect_external_tool_intent(
        user_message,
    )

    if intent is None:
        return None

    tool_name, _ = intent

    return PlannerResult(
        route="tool",
        confidence=1.0,
        reasoning=(
            "Selected the 'tool' route because the request can "
            f"be handled deterministically by the '{tool_name}' tool."
        ),
        signals=[
            tool_name,
        ],
    )

from __future__ import annotations

from app.mcp.planner_intent import (
    MCPToolIntent,
    detect_available_mcp_tool_intent,
)
from app.schemas.planner import PlannerResult


class MCPPlannerService:
    """Create deterministic plans for available MCP tools."""

    @staticmethod
    async def create_plan(
        user_message: str,
    ) -> tuple[
        PlannerResult,
        MCPToolIntent,
    ] | None:
        intent = await detect_available_mcp_tool_intent(
            user_message,
        )

        if intent is None:
            return None

        return (
            PlannerResult(
                route="tool",
                confidence=1.0,
                reasoning=(
                    "Selected the 'tool' route because the request "
                    "matches an available MCP filesystem capability."
                ),
                signals=[
                    intent.matched_signal,
                    intent.qualified_name,
                    "mcp",
                ],
            ),
            intent,
        )

from __future__ import annotations

import json

from app.mcp.planner_intent import (
    MCPToolIntent,
    detect_available_mcp_tool_intent,
)
from app.schemas.planner import PlannerResult
from app.services.dynamic_mcp_selector import (
    DynamicMCPSelector,
)


TOOL_ARGUMENTS_SIGNAL_PREFIX = (
    "tool_arguments_json:"
)


class MCPPlannerService:
    """
    Plan MCP execution.

    Fast path:
    - deterministic Filesystem MCP intent extraction.

    Generic path:
    - dynamic selection from the live Unified Tool Catalog.
    """

    @staticmethod
    async def create_plan(
        user_message: str,
    ) -> tuple[
        PlannerResult,
        MCPToolIntent | None,
    ] | None:
        intent = await detect_available_mcp_tool_intent(
            user_message,
        )

        if intent is not None:
            return (
                PlannerResult(
                    route="tool",
                    confidence=1.0,
                    reasoning=(
                        "Selected the 'tool' route because the "
                        "request matches an available MCP capability."
                    ),
                    signals=[
                        intent.matched_signal,
                        intent.qualified_name,
                        "mcp",
                        (
                            TOOL_ARGUMENTS_SIGNAL_PREFIX
                            + json.dumps(
                                intent.arguments,
                                ensure_ascii=False,
                                separators=(
                                    ",",
                                    ":",
                                ),
                            )
                        ),
                    ],
                ),
                intent,
            )

        dynamic_selection = (
            await DynamicMCPSelector.select(
                user_message=user_message,
            )
        )

        if dynamic_selection is None:
            return None

        qualified_name = str(
            dynamic_selection.qualified_name,
        )

        return (
            PlannerResult(
                route="tool",
                confidence=(
                    dynamic_selection.confidence
                ),
                reasoning=(
                    "Selected the 'tool' route using dynamic MCP "
                    "catalog matching. "
                    + dynamic_selection.reasoning
                ),
                signals=[
                    "dynamic mcp selection",
                    qualified_name,
                    "mcp",
                    (
                        TOOL_ARGUMENTS_SIGNAL_PREFIX
                        + json.dumps(
                            dynamic_selection.arguments,
                            ensure_ascii=False,
                            separators=(
                                ",",
                                ":",
                            ),
                        )
                    ),
                ],
            ),
            None,
        )

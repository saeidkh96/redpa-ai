from __future__ import annotations

import logging
import re
from typing import Any

from app.agents.state import AgentState
from app.formatters.mcp_tool_formatter import (
    format_mcp_tool_response,
)
from app.formatters.tool_formatter import (
    format_tool_response,
)
from app.mcp.planner_intent import (
    detect_mcp_tool_intent,
)
from app.services.mcp_service import MCPService
from app.services.tool_service import ToolService
from app.tools.intent import detect_external_tool_intent


logger = logging.getLogger(__name__)


CALCULATOR_KEYWORDS = (
    "calculate",
    "calculator",
    "compute",
    "evaluate",
    "solve",
)

DATETIME_KEYWORDS = (
    "what time",
    "current time",
    "time now",
    "what is the time",
    "today's date",
    "todays date",
    "current date",
    "what date",
    "what day",
    "date today",
    "weekday",
)


async def tool_node(
    state: AgentState,
) -> dict[str, object]:
    selected_tool = _resolve_selected_tool(
        state,
    )

    if selected_tool is None:
        error_message = (
            "No supported tool could be selected for this request."
        )

        return {
            "selected_tool": None,
            "tool_arguments": None,
            "tool_success": False,
            "tool_result": None,
            "tool_error": error_message,
            "tool_execution_time_ms": 0.0,
            "tool_metadata": None,
            "response_content": (
                "I understood that this request requires a tool, "
                "but I could not determine which available tool "
                "should be used."
            ),
            "provider": "redpa-tool-runtime",
            "model": "tool-router",
            "usage": {},
            "completed": False,
            "error": error_message,
        }

    arguments = _resolve_tool_arguments(
        state=state,
        selected_tool=selected_tool,
    )

    if selected_tool.startswith(
        "mcp:",
    ):
        return await _execute_mcp_tool(
            state=state,
            selected_tool=selected_tool,
            arguments=arguments,
        )

    execution_result = await ToolService.execute(
        tool_name=selected_tool,
        arguments=arguments,
    )

    return {
        "selected_tool": selected_tool,
        "tool_arguments": arguments,
        "tool_result": execution_result.result,
        "tool_success": execution_result.success,
        "tool_error": execution_result.error,
        "tool_execution_time_ms": (
            execution_result.execution_time_ms
        ),
        "tool_metadata": execution_result.metadata,
        "response_content": format_tool_response(
            tool_name=selected_tool,
            success=execution_result.success,
            result=execution_result.result,
            error=execution_result.error,
            arguments=arguments,
        ),
        "provider": "redpa-tool-runtime",
        "model": selected_tool,
        "usage": {
            "tool_name": selected_tool,
            "tool_source": "internal",
            "execution_time_ms": (
                execution_result.execution_time_ms
            ),
        },
        "completed": execution_result.success,
        "error": execution_result.error,
    }


async def _execute_mcp_tool(
    *,
    state: AgentState,
    selected_tool: str,
    arguments: dict[str, Any],
) -> dict[str, object]:
    try:
        execution_result = (
            await MCPService.call_qualified_tool(
                qualified_name=selected_tool,
                arguments=arguments,
                approval_granted=bool(
                    state.get(
                        "approval_granted",
                        False,
                    )
                ),
            )
        )

        error_message = (
            None
            if execution_result.success
            else _extract_mcp_error(
                execution_result.content,
            )
        )

        return {
            "selected_tool": selected_tool,
            "tool_arguments": arguments,
            "tool_result": (
                execution_result.structured_content
                if execution_result.structured_content
                is not None
                else execution_result.content
            ),
            "tool_success": execution_result.success,
            "tool_error": error_message,
            "tool_execution_time_ms": (
                execution_result.execution_time_ms
            ),
            "tool_metadata": {
                "source": "mcp",
                "server_name": (
                    execution_result.server_name
                ),
                "tool_name": (
                    execution_result.tool_name
                ),
                "qualified_name": selected_tool,
                "is_error": execution_result.is_error,
            },
            "response_content": format_mcp_tool_response(
                qualified_name=selected_tool,
                success=execution_result.success,
                structured_content=(
                    execution_result.structured_content
                ),
                content=execution_result.content,
                error=error_message,
            ),
            "provider": "redpa-mcp-runtime",
            "model": selected_tool,
            "usage": {
                "tool_name": selected_tool,
                "tool_source": "mcp",
                "mcp_server": (
                    execution_result.server_name
                ),
                "execution_time_ms": (
                    execution_result.execution_time_ms
                ),
            },
            "completed": execution_result.success,
            "error": error_message,
        }

    except Exception as exception:
        error_message = (
            f"{type(exception).__name__}: "
            f"{str(exception).strip() or 'Unknown MCP error.'}"
        )[:1000]

        logger.exception(
            "MCP tool execution failed "
            "| tool=%s error=%s",
            selected_tool,
            error_message,
        )

        return {
            "selected_tool": selected_tool,
            "tool_arguments": arguments,
            "tool_result": None,
            "tool_success": False,
            "tool_error": error_message,
            "tool_execution_time_ms": 0.0,
            "tool_metadata": {
                "source": "mcp",
                "qualified_name": selected_tool,
            },
            "response_content": (
                f"The MCP tool `{selected_tool}` could not "
                f"complete the request: {error_message}"
            ),
            "provider": "redpa-mcp-runtime",
            "model": selected_tool,
            "usage": {
                "tool_name": selected_tool,
                "tool_source": "mcp",
                "execution_time_ms": 0.0,
            },
            "completed": False,
            "error": error_message,
        }


def _resolve_selected_tool(
    state: AgentState,
) -> str | None:
    selected = _optional_string(
        state.get(
            "selected_tool",
        )
    )

    if selected:
        return selected.casefold()

    payload = state.get(
        "action_payload",
    )

    if isinstance(
        payload,
        dict,
    ):
        payload_tool = (
            _optional_string(
                payload.get(
                    "tool_name",
                )
            )
            or _optional_string(
                payload.get(
                    "tool",
                )
            )
        )

        if payload_tool:
            return payload_tool.casefold()

    signals = state.get(
        "planner_signals",
        [],
    )

    if isinstance(
        signals,
        list,
    ):
        normalized_signals = [
            str(
                signal,
            ).strip().casefold()
            for signal in signals
            if str(
                signal,
            ).strip()
        ]

        for signal in normalized_signals:
            if signal.startswith(
                "mcp:",
            ):
                return signal

        for tool_name in (
            "weather",
            "currency",
            "github",
            "datetime",
            "calculator",
            "news",
            "web_search",
        ):
            if tool_name in normalized_signals:
                return tool_name

    request_content = _get_request_content(
        state,
    )

    if not request_content:
        return None

    mcp_intent = detect_mcp_tool_intent(
        request_content,
    )

    if mcp_intent is not None:
        return mcp_intent.qualified_name

    external_intent = detect_external_tool_intent(
        request_content,
    )

    if external_intent:
        return external_intent[0]

    lowered = request_content.casefold()

    if _is_datetime_request(
        lowered,
    ):
        return "datetime"

    if _is_calculator_request(
        request_content,
    ):
        return "calculator"

    return None


def _resolve_tool_arguments(
    *,
    state: AgentState,
    selected_tool: str,
) -> dict[str, Any]:
    existing = state.get(
        "tool_arguments",
    )

    if isinstance(
        existing,
        dict,
    ) and existing:
        return existing

    payload = state.get(
        "action_payload",
    )

    if isinstance(
        payload,
        dict,
    ):
        payload_arguments = payload.get(
            "arguments",
        )

        if isinstance(
            payload_arguments,
            dict,
        ) and payload_arguments:
            return payload_arguments

    request_content = (
        _get_request_content(
            state,
        )
        or ""
    )

    if selected_tool.startswith(
        "mcp:",
    ):
        mcp_intent = detect_mcp_tool_intent(
            request_content,
        )

        if (
            mcp_intent is not None
            and mcp_intent.qualified_name.casefold()
            == selected_tool.casefold()
        ):
            return mcp_intent.arguments

        return {}

    external_intent = detect_external_tool_intent(
        request_content,
    )

    if (
        external_intent
        and external_intent[0]
        == selected_tool
    ):
        return external_intent[1]

    if selected_tool == "calculator":
        expression = _extract_math_expression(
            request_content,
        )

        return {
            "expression": (
                expression
                or _strip_calculator_command(
                    request_content,
                )
            )
        }

    if selected_tool == "datetime":
        return {
            "timezone": _extract_timezone(
                request_content,
            )
        }

    return {}


def _get_request_content(
    state: AgentState,
) -> str | None:
    request_content = _optional_string(
        state.get(
            "request_content",
        )
    )

    if request_content:
        return request_content

    for message in reversed(
        state.get(
            "messages",
            [],
        )
    ):
        if not isinstance(
            message,
            dict,
        ):
            continue

        if message.get(
            "role",
        ) != "user":
            continue

        content = _optional_string(
            message.get(
                "content",
            )
        )

        if content:
            return content

    return None


def _extract_mcp_error(
    content: list[dict[str, Any]],
) -> str | None:
    for item in content:
        if not isinstance(
            item,
            dict,
        ):
            continue

        text = item.get(
            "text",
        )

        if text:
            return str(
                text,
            ).strip()

    return None


def _is_datetime_request(
    text: str,
) -> bool:
    return (
        any(
            keyword in text
            for keyword in DATETIME_KEYWORDS
        )
        or bool(
            re.search(
                r"\b(time|date|day)\b.*\b(in|for)\b",
                text,
            )
        )
    )


def _is_calculator_request(
    text: str,
) -> bool:
    lowered = text.casefold()

    return (
        any(
            keyword in lowered
            for keyword in CALCULATOR_KEYWORDS
        )
        or (
            _extract_math_expression(
                text,
            )
            is not None
        )
    )


def _extract_math_expression(
    text: str,
) -> str | None:
    candidates = re.findall(
        r"(?<![\w.])[-+]?(?:\d+(?:\.\d+)?|\.\d+)"
        r"(?:\s*(?:\*\*|[+\-*/%])\s*"
        r"(?:\d+(?:\.\d+)?|\.\d+))+(?![\w.])",
        text.strip(),
    )

    return (
        candidates[-1].strip()
        if candidates
        else None
    )


def _strip_calculator_command(
    text: str,
) -> str:
    return re.sub(
        r"(?i)^\s*(please\s+)?"
        r"(calculate|calculator|compute|evaluate|solve|what\s+is)\s*",
        "",
        text,
    ).strip()


def _extract_timezone(
    text: str,
) -> str:
    lowered = text.casefold()

    aliases = {
        "new york": "America/New_York",
        "berlin": "Europe/Berlin",
        "germany": "Europe/Berlin",
        "passau": "Europe/Berlin",
        "london": "Europe/London",
        "paris": "Europe/Paris",
        "tokyo": "Asia/Tokyo",
        "tehran": "Asia/Tehran",
        "iran": "Asia/Tehran",
        "utc": "UTC",
        "gmt": "UTC",
    }

    for alias, timezone in aliases.items():
        if alias in lowered:
            return timezone

    match = re.search(
        r"\b([A-Za-z_]+/[A-Za-z_+\-]+)\b",
        text,
    )

    return (
        match.group(
            1,
        )
        if match
        else "UTC"
    )


def _optional_string(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = str(
        value,
    ).strip()

    return (
        normalized
        or None
    )

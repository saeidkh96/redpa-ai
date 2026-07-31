from __future__ import annotations

import logging
import re
from typing import Any

from app.agents.state import AgentState
from app.services.tool_service import ToolService


logger = logging.getLogger(__name__)


CALCULATOR_KEYWORDS: tuple[str, ...] = (
    "calculate",
    "calculator",
    "compute",
    "evaluate",
    "solve",
)

DATETIME_KEYWORDS: tuple[str, ...] = (
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
    """
    Select and execute a registered RedPA tool.
    """

    selected_tool = _resolve_selected_tool(
        state,
    )

    if selected_tool is None:
        error_message = (
            "No supported tool could be selected for this request."
        )

        logger.warning(
            "Tool selection failed | planner_signals=%s "
            "request_content=%s",
            state.get("planner_signals"),
            _get_request_content(state),
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

    tool_arguments = _resolve_tool_arguments(
        state=state,
        selected_tool=selected_tool,
    )

    execution_result = await ToolService.execute(
        tool_name=selected_tool,
        arguments=tool_arguments,
    )

    response_content = _build_tool_response(
        tool_name=selected_tool,
        success=execution_result.success,
        result=execution_result.result,
        error=execution_result.error,
        arguments=tool_arguments,
    )

    return {
        "selected_tool": selected_tool,
        "tool_arguments": tool_arguments,
        "tool_result": execution_result.result,
        "tool_success": execution_result.success,
        "tool_error": execution_result.error,
        "tool_execution_time_ms": (
            execution_result.execution_time_ms
        ),
        "tool_metadata": execution_result.metadata,
        "response_content": response_content,
        "provider": "redpa-tool-runtime",
        "model": selected_tool,
        "usage": {
            "tool_name": selected_tool,
            "execution_time_ms": (
                execution_result.execution_time_ms
            ),
        },
        "completed": execution_result.success,
        "error": execution_result.error,
    }


def _resolve_selected_tool(
    state: AgentState,
) -> str | None:
    selected_tool = _optional_string(
        state.get(
            "selected_tool",
        )
    )

    if selected_tool:
        return selected_tool.casefold()

    action_payload = state.get(
        "action_payload",
    )

    if isinstance(
        action_payload,
        dict,
    ):
        payload_tool_name = (
            _optional_string(
                action_payload.get(
                    "tool_name",
                )
            )
            or _optional_string(
                action_payload.get(
                    "tool",
                )
            )
        )

        if payload_tool_name:
            return payload_tool_name.casefold()

    planner_signals = state.get(
        "planner_signals",
        [],
    )

    if isinstance(
        planner_signals,
        list,
    ):
        normalized_signals = {
            str(signal).strip().casefold()
            for signal in planner_signals
            if str(signal).strip()
        }

        if "datetime" in normalized_signals:
            return "datetime"

        if "calculator" in normalized_signals:
            return "calculator"

    request_content = _get_request_content(
        state,
    )

    if request_content is None:
        return None

    normalized_request = request_content.casefold()

    if _is_datetime_request(
        normalized_request,
    ):
        return "datetime"

    if _is_calculator_request(
        request_content,
    ):
        return "calculator"

    return None


def _is_datetime_request(
    normalized_request: str,
) -> bool:
    if any(
        keyword in normalized_request
        for keyword in DATETIME_KEYWORDS
    ):
        return True

    return bool(
        re.search(
            r"\b(time|date|day)\b.*\b(in|for)\b",
            normalized_request,
        )
    )


def _is_calculator_request(
    request_content: str,
) -> bool:
    normalized_request = request_content.casefold()

    if any(
        keyword in normalized_request
        for keyword in CALCULATOR_KEYWORDS
    ):
        return True

    return (
        _extract_math_expression(
            request_content,
        )
        is not None
    )


def _resolve_tool_arguments(
    *,
    state: AgentState,
    selected_tool: str,
) -> dict[str, Any]:
    existing_arguments = state.get(
        "tool_arguments",
    )

    if isinstance(
        existing_arguments,
        dict,
    ) and existing_arguments:
        return existing_arguments

    action_payload = state.get(
        "action_payload",
    )

    if isinstance(
        action_payload,
        dict,
    ):
        payload_arguments = action_payload.get(
            "arguments",
        )

        if isinstance(
            payload_arguments,
            dict,
        ) and payload_arguments:
            return payload_arguments

        if selected_tool == "calculator":
            expression = _optional_string(
                action_payload.get(
                    "expression",
                )
            )

            if expression:
                return {
                    "expression": expression,
                }

        if selected_tool == "datetime":
            timezone = _optional_string(
                action_payload.get(
                    "timezone",
                )
            )

            if timezone:
                return {
                    "timezone": timezone,
                }

    request_content = _get_request_content(
        state,
    )

    if (
        selected_tool == "calculator"
        and request_content
    ):
        expression = _extract_math_expression(
            request_content,
        )

        if expression:
            return {
                "expression": expression,
            }

        return {
            "expression": _strip_calculator_command(
                request_content,
            ),
        }

    if (
        selected_tool == "datetime"
        and request_content
    ):
        return {
            "timezone": _extract_timezone(
                request_content,
            ),
        }

    if selected_tool == "datetime":
        return {
            "timezone": "UTC",
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

    messages = state.get(
        "messages",
        [],
    )

    for message in reversed(
        messages,
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


def _extract_math_expression(
    text: str,
) -> str | None:
    normalized_text = text.strip()

    if not normalized_text:
        return None

    expression_candidates = re.findall(
        r"(?<![\w.])"
        r"[-+]?"
        r"(?:\d+(?:\.\d+)?|\.\d+)"
        r"(?:\s*(?:\*\*|[+\-*/%])\s*"
        r"(?:\d+(?:\.\d+)?|\.\d+))+"
        r"(?![\w.])",
        normalized_text,
    )

    if expression_candidates:
        return expression_candidates[-1].strip()

    return None


def _strip_calculator_command(
    text: str,
) -> str:
    cleaned_text = re.sub(
        r"(?i)^\s*"
        r"(please\s+)?"
        r"(calculate|calculator|compute|evaluate|solve|what\s+is)"
        r"\s*",
        "",
        text,
    )

    return cleaned_text.strip()


def _extract_timezone(
    text: str,
) -> str:
    normalized_text = text.strip()
    lowered_text = normalized_text.casefold()

    aliases_in_text: dict[str, str] = {
        "new york": "America/New_York",
        "new_york": "America/New_York",
        "newyork": "America/New_York",
        "berlin": "Europe/Berlin",
        "germany": "Europe/Berlin",
        "deutschland": "Europe/Berlin",
        "passau": "Europe/Berlin",
        "london": "Europe/London",
        "paris": "Europe/Paris",
        "tokyo": "Asia/Tokyo",
        "tehran": "Asia/Tehran",
        "iran": "Asia/Tehran",
        "utc": "UTC",
        "gmt": "UTC",
    }

    for alias, timezone_name in aliases_in_text.items():
        if alias in lowered_text:
            return timezone_name

    iana_match = re.search(
        r"\b([A-Za-z_]+/[A-Za-z_+\-]+)\b",
        normalized_text,
    )

    if iana_match is not None:
        return iana_match.group(1)

    return "UTC"


def _build_tool_response(
    *,
    tool_name: str,
    success: bool,
    result: Any,
    error: str | None,
    arguments: dict[str, Any],
) -> str:
    if not success:
        if tool_name == "calculator":
            return (
                "The calculator rejected the expression because "
                "it contains invalid or unsupported operations. "
                f"Error: {error or 'Invalid expression.'}"
            )

        if tool_name == "datetime":
            return (
                "The datetime tool could not complete the request. "
                f"Error: {error or 'Unknown datetime error.'}"
            )

        return (
            f"The '{tool_name}' tool could not complete the "
            f"request. Error: {error or 'Unknown tool error.'}"
        )

    if tool_name == "calculator":
        expression = arguments.get(
            "expression",
            "",
        )

        return (
            f"The result of {expression} is {result}."
        )

    if tool_name == "datetime":
        if not isinstance(
            result,
            dict,
        ):
            return (
                "The datetime tool completed successfully."
            )

        return (
            f"The current time in "
            f"{result.get('timezone', 'UTC')} is "
            f"{result.get('time', '')} on "
            f"{result.get('date', '')}. "
            f"It is {result.get('weekday', '')}."
        )

    return (
        f"The '{tool_name}' tool completed successfully. "
        f"Result: {result}"
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
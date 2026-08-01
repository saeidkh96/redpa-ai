from __future__ import annotations

import logging
import re
from typing import Any

from app.agents.state import AgentState
from app.services.tool_service import ToolService
from app.tools.intent import detect_external_tool_intent


logger = logging.getLogger(__name__)


CALCULATOR_KEYWORDS = (
    "calculate", "calculator", "compute", "evaluate", "solve",
)

DATETIME_KEYWORDS = (
    "what time", "current time", "time now", "what is the time",
    "today's date", "todays date", "current date", "what date",
    "what day", "date today", "weekday",
)


async def tool_node(state: AgentState) -> dict[str, object]:
    selected_tool = _resolve_selected_tool(state)

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
        "tool_execution_time_ms": execution_result.execution_time_ms,
        "tool_metadata": execution_result.metadata,
        "response_content": _build_tool_response(
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
            "execution_time_ms": execution_result.execution_time_ms,
        },
        "completed": execution_result.success,
        "error": execution_result.error,
    }


def _resolve_selected_tool(state: AgentState) -> str | None:
    selected = _optional_string(state.get("selected_tool"))
    if selected:
        return selected.casefold()

    payload = state.get("action_payload")
    if isinstance(payload, dict):
        payload_tool = (
            _optional_string(payload.get("tool_name"))
            or _optional_string(payload.get("tool"))
        )
        if payload_tool:
            return payload_tool.casefold()

    signals = state.get("planner_signals", [])
    if isinstance(signals, list):
        normalized = {
            str(signal).strip().casefold()
            for signal in signals
            if str(signal).strip()
        }
        for tool_name in (
            "weather", "currency", "github", "datetime", "calculator",
        ):
            if tool_name in normalized:
                return tool_name

    request_content = _get_request_content(state)
    if not request_content:
        return None

    external_intent = detect_external_tool_intent(request_content)
    if external_intent:
        return external_intent[0]

    lowered = request_content.casefold()
    if _is_datetime_request(lowered):
        return "datetime"
    if _is_calculator_request(request_content):
        return "calculator"

    return None


def _resolve_tool_arguments(
    *,
    state: AgentState,
    selected_tool: str,
) -> dict[str, Any]:
    existing = state.get("tool_arguments")
    if isinstance(existing, dict) and existing:
        return existing

    payload = state.get("action_payload")
    if isinstance(payload, dict):
        payload_arguments = payload.get("arguments")
        if isinstance(payload_arguments, dict) and payload_arguments:
            return payload_arguments

    request_content = _get_request_content(state) or ""

    external_intent = detect_external_tool_intent(request_content)
    if external_intent and external_intent[0] == selected_tool:
        return external_intent[1]

    if selected_tool == "calculator":
        expression = _extract_math_expression(request_content)
        return {
            "expression": (
                expression
                or _strip_calculator_command(request_content)
            )
        }

    if selected_tool == "datetime":
        return {"timezone": _extract_timezone(request_content)}

    return {}


def _get_request_content(state: AgentState) -> str | None:
    request_content = _optional_string(state.get("request_content"))
    if request_content:
        return request_content

    for message in reversed(state.get("messages", [])):
        if not isinstance(message, dict):
            continue
        if message.get("role") != "user":
            continue
        content = _optional_string(message.get("content"))
        if content:
            return content

    return None


def _is_datetime_request(text: str) -> bool:
    return any(keyword in text for keyword in DATETIME_KEYWORDS) or bool(
        re.search(r"\b(time|date|day)\b.*\b(in|for)\b", text)
    )


def _is_calculator_request(text: str) -> bool:
    lowered = text.casefold()
    return any(keyword in lowered for keyword in CALCULATOR_KEYWORDS) or (
        _extract_math_expression(text) is not None
    )


def _extract_math_expression(text: str) -> str | None:
    candidates = re.findall(
        r"(?<![\w.])[-+]?(?:\d+(?:\.\d+)?|\.\d+)"
        r"(?:\s*(?:\*\*|[+\-*/%])\s*"
        r"(?:\d+(?:\.\d+)?|\.\d+))+(?![\w.])",
        text.strip(),
    )
    return candidates[-1].strip() if candidates else None


def _strip_calculator_command(text: str) -> str:
    return re.sub(
        r"(?i)^\s*(please\s+)?"
        r"(calculate|calculator|compute|evaluate|solve|what\s+is)\s*",
        "",
        text,
    ).strip()


def _extract_timezone(text: str) -> str:
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
    match = re.search(r"\b([A-Za-z_]+/[A-Za-z_+\-]+)\b", text)
    return match.group(1) if match else "UTC"


def _build_tool_response(
    *,
    tool_name: str,
    success: bool,
    result: Any,
    error: str | None,
    arguments: dict[str, Any],
) -> str:
    if not success:
        return (
            f"The '{tool_name}' tool could not complete the request. "
            f"Error: {error or 'Unknown tool error.'}"
        )

    if tool_name == "calculator":
        return (
            f"The result of {arguments.get('expression', '')} "
            f"is {result}."
        )

    if tool_name == "datetime" and isinstance(result, dict):
        return (
            f"The current time in {result.get('timezone', 'UTC')} is "
            f"{result.get('time', '')} on {result.get('date', '')}. "
            f"It is {result.get('weekday', '')}."
        )

    if tool_name == "weather" and isinstance(result, dict):
        location = result.get("location", {})
        return (
            f"The current weather in {location.get('name', '')}, "
            f"{location.get('country', '')} is "
            f"{result.get('condition', '')}, "
            f"{result.get('temperature')} "
            f"{result.get('temperature_unit', '')}. "
            f"It feels like {result.get('apparent_temperature')} "
            f"{result.get('temperature_unit', '')}."
        )

    if tool_name == "currency" and isinstance(result, dict):
        return (
            f"{result.get('amount')} {result.get('from_currency')} "
            f"is {result.get('converted_amount')} "
            f"{result.get('to_currency')} using the reference rate "
            f"{result.get('rate')}."
        )

    if tool_name == "github" and isinstance(result, dict):
        return (
            f"GitHub repository {result.get('full_name')} has "
            f"{result.get('stars')} stars, {result.get('forks')} forks, "
            f"and uses {result.get('language') or 'no primary language'}."
        )

    return f"The '{tool_name}' tool completed successfully. Result: {result}"


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None

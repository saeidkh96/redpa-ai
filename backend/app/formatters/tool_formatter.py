from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.formatters.currency import (
    format_currency_result,
)
from app.formatters.github import (
    format_github_result,
)
from app.formatters.news import (
    format_news_result,
)
from app.formatters.weather import (
    format_weather_result,
)
from app.formatters.web_search import (
    format_web_search_result,
)


ToolFormatter = Callable[
    [dict[str, Any]],
    str,
]


FORMATTERS: dict[str, ToolFormatter] = {
    "weather": format_weather_result,
    "currency": format_currency_result,
    "github": format_github_result,
    "news": format_news_result,
    "web_search": format_web_search_result,
}


def format_tool_response(
    *,
    tool_name: str,
    success: bool,
    result: Any,
    error: str | None,
    arguments: dict[str, Any],
) -> str:
    normalized_tool_name = str(
        tool_name or "unknown",
    ).strip().casefold()

    if not success:
        return (
            f"The '{normalized_tool_name}' tool could not "
            "complete the request. "
            f"Error: {error or 'Unknown tool error.'}"
        )

    if normalized_tool_name == "calculator":
        return (
            f"The result of "
            f"{arguments.get('expression', '')} "
            f"is {result}."
        )

    if (
        normalized_tool_name == "datetime"
        and isinstance(result, dict)
    ):
        return (
            f"The current time in "
            f"{result.get('timezone', 'UTC')} is "
            f"{result.get('time', '')} on "
            f"{result.get('date', '')}. "
            f"It is {result.get('weekday', '')}."
        )

    if not isinstance(result, dict):
        return (
            f"The '{normalized_tool_name}' tool completed "
            f"successfully. Result: {result}"
        )

    formatter = FORMATTERS.get(
        normalized_tool_name,
    )

    if formatter is None:
        return (
            f"The '{normalized_tool_name}' tool completed "
            f"successfully. Result: {result}"
        )

    return formatter(
        result,
    )

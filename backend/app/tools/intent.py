from __future__ import annotations

import re
from typing import Any

from app.tools.search_intent import (
    detect_search_tool_intent,
)


def detect_external_tool_intent(
    text: str,
) -> tuple[str, dict[str, Any]] | None:
    """
    Detect supported external-tool requests and extract arguments.

    The order is intentional:
    web-search/news requests are checked before more general patterns.
    """

    cleaned_text = str(
        text or "",
    ).strip()

    if not cleaned_text:
        return None

    search_intent = detect_search_tool_intent(
        cleaned_text,
    )

    if search_intent is not None:
        return search_intent

    weather_match = re.search(
        r"(?:what(?:'s|\s+is)\s+the\s+)?"
        r"(?:current\s+)?"
        r"(?:weather|temperature|forecast)"
        r"(?:\s+(?:in|for|at))?\s+"
        r"(.+?)[?.!]*$",
        cleaned_text,
        flags=re.IGNORECASE,
    )

    if weather_match is not None:
        location = weather_match.group(
            1,
        ).strip(
            " ?.!",
        )

        if location:
            return (
                "weather",
                {
                    "location": location,
                },
            )

    currency_match = re.search(
        r"(?:convert\s+)?"
        r"([0-9]+(?:\.[0-9]+)?)\s*"
        r"([A-Za-z]{3})\s+"
        r"(?:to|in)\s+"
        r"([A-Za-z]{3})",
        cleaned_text,
        flags=re.IGNORECASE,
    )

    if currency_match is not None:
        return (
            "currency",
            {
                "amount": currency_match.group(
                    1,
                ),
                "from_currency": currency_match.group(
                    2,
                ).upper(),
                "to_currency": currency_match.group(
                    3,
                ).upper(),
            },
        )

    github_url_match = re.search(
        r"https://github\.com/"
        r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",
        cleaned_text,
        flags=re.IGNORECASE,
    )

    if github_url_match is not None:
        return (
            "github",
            {
                "repository": github_url_match.group(
                    1,
                ),
            },
        )

    github_match = re.search(
        r"(?:show|get|find)?\s*"
        r"(?:github\s+)?"
        r"(?:repository|repo)"
        r"(?:\s+(?:info|information))?"
        r"(?:\s+(?:for|about))?\s+"
        r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",
        cleaned_text,
        flags=re.IGNORECASE,
    )

    if github_match is not None:
        return (
            "github",
            {
                "repository": github_match.group(
                    1,
                ),
            },
        )

    return None

from __future__ import annotations

import re
from typing import Any


def detect_search_tool_intent(
    text: str,
) -> tuple[str, dict[str, Any]] | None:
    cleaned = str(text or "").strip()

    news_match = re.search(
        r"(?:latest|top|current)?\s*"
        r"(?:hacker\s*news|tech\s+news|technology\s+news)"
        r"(?:\s+stories)?",
        cleaned,
        flags=re.IGNORECASE,
    )
    if news_match:
        return "news", {"limit": 5}

    search_match = re.search(
        r"(?:search\s+the\s+web\s+for|"
        r"search\s+online\s+for|web\s+search\s+for|"
        r"look\s+up\s+online)\s+(.+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if search_match:
        return "web_search", {
            "query": search_match.group(1).strip(" ?.!")
        }

    return None

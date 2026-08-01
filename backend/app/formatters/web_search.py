from __future__ import annotations

from typing import Any


def format_web_search_result(
    result: dict[str, Any],
) -> str:
    query = result.get("query")
    results = result.get("results", [])

    if not isinstance(results, list) or not results:
        if query:
            return (
                "No web results were found for: "
                f"{query}"
            )

        return "No web results were found."

    lines = [
        (
            f"Web search results for: {query}"
            if query
            else "Web search results"
        ),
        "",
    ]

    for index, item in enumerate(
        results,
        start=1,
    ):
        if not isinstance(item, dict):
            continue

        lines.append(
            f"{index}. "
            f"{item.get('title') or 'Untitled result'}"
        )

        description = item.get("description")

        if description:
            lines.append(
                f"   {description}"
            )

        url = item.get("url")

        if url:
            lines.append(
                f"   {url}"
            )

        age = item.get("age")

        if age:
            lines.append(
                f"   Published: {age}"
            )

        lines.append("")

    provider = result.get("provider")

    if provider:
        lines.append(
            f"Provider: {provider}"
        )

    return "\n".join(lines).strip()

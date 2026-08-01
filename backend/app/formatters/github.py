from __future__ import annotations

from typing import Any


def format_github_result(
    result: dict[str, Any],
) -> str:
    full_name = (
        result.get("full_name")
        or "Unknown repository"
    )

    lines = [
        f"GitHub repository: {full_name}",
        "",
    ]

    description = result.get("description")

    if description:
        lines.extend(
            [
                str(description),
                "",
            ]
        )

    lines.extend(
        [
            f"Language: {result.get('language') or 'Not specified'}",
            f"Stars: {result.get('stars', 0)}",
            f"Forks: {result.get('forks', 0)}",
            f"Open issues: {result.get('open_issues', 0)}",
        ]
    )

    default_branch = result.get(
        "default_branch",
    )

    if default_branch:
        lines.append(
            f"Default branch: {default_branch}"
        )

    license_name = result.get("license")

    if license_name:
        lines.append(
            f"License: {license_name}"
        )

    topics = result.get("topics", [])

    if isinstance(topics, list) and topics:
        lines.append(
            "Topics: "
            + ", ".join(
                str(topic)
                for topic in topics[:10]
            )
        )

    html_url = result.get("html_url")

    if html_url:
        lines.extend(
            [
                "",
                str(html_url),
            ]
        )

    return "\n".join(lines)

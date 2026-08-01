from __future__ import annotations

from typing import Any


def format_news_result(
    result: dict[str, Any],
) -> str:
    stories = result.get("stories", [])

    if not isinstance(stories, list) or not stories:
        return "No news stories were returned."

    lines = [
        "Latest Hacker News stories",
        "",
    ]

    for index, story in enumerate(
        stories,
        start=1,
    ):
        if not isinstance(story, dict):
            continue

        lines.append(
            f"{index}. "
            f"{story.get('title') or 'Untitled story'}"
        )

        metadata_parts = []

        score = story.get("score")

        if score is not None:
            metadata_parts.append(
                f"Score: {score}"
            )

        comments = story.get("comments")

        if comments is not None:
            metadata_parts.append(
                f"Comments: {comments}"
            )

        author = story.get("author")

        if author:
            metadata_parts.append(
                f"Author: {author}"
            )

        if metadata_parts:
            lines.append(
                "   " + " | ".join(metadata_parts)
            )

        url = story.get("url")

        if url:
            lines.append(
                f"   {url}"
            )

        lines.append("")

    provider = result.get("provider")

    if provider:
        lines.append(
            f"Provider: {provider}"
        )

    return "\n".join(lines).strip()

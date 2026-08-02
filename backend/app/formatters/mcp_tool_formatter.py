from __future__ import annotations

from typing import Any


def format_mcp_tool_response(
    *,
    qualified_name: str,
    success: bool,
    structured_content: Any,
    content: list[dict[str, Any]],
    error: str | None,
) -> str:
    if not success:
        message = (
            error
            or _first_text_content(
                content,
            )
            or "The MCP tool could not complete the request."
        )

        return (
            f"MCP tool `{qualified_name}` failed: {message}"
        )

    tool_name = qualified_name.rsplit(
        ":",
        1,
    )[-1]

    if tool_name == "list_files":
        return _format_file_list(
            structured_content,
        )

    if tool_name == "read_file":
        return _format_read_file(
            structured_content,
        )

    if tool_name == "search_files":
        return _format_search_results(
            structured_content,
        )

    if tool_name == "file_info":
        return _format_file_info(
            structured_content,
        )

    text_content = _first_text_content(
        content,
    )

    if text_content:
        return text_content

    return (
        f"MCP tool `{qualified_name}` completed successfully."
    )


def _format_file_list(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "The filesystem listing completed successfully."

    entries = result.get(
        "entries",
        [],
    )

    if not isinstance(
        entries,
        list,
    ) or not entries:
        return (
            f"No visible files were found in "
            f"`{result.get('path', '.')}`."
        )

    lines = [
        f"Files in `{result.get('path', '.')}`:",
        "",
    ]

    for entry in entries:
        if not isinstance(
            entry,
            dict,
        ):
            continue

        entry_type = entry.get(
            "type",
            "file",
        )

        marker = (
            "📁"
            if entry_type == "directory"
            else "📄"
        )

        lines.append(
            f"- {marker} `{entry.get('path', entry.get('name', 'unknown'))}`"
        )

    if result.get(
        "truncated",
        False,
    ):
        lines.extend(
            [
                "",
                "The result was truncated.",
            ]
        )

    return "\n".join(
        lines,
    )


def _format_read_file(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "The file was read successfully."

    path = result.get(
        "path",
        "file",
    )

    content = str(
        result.get(
            "content",
            "",
        )
        or ""
    )

    if not content:
        return (
            f"`{path}` is empty or contains no readable text."
        )

    suffix = str(
        path,
    ).rsplit(
        ".",
        1,
    )[-1].casefold()

    language = {
        "py": "python",
        "json": "json",
        "yml": "yaml",
        "yaml": "yaml",
        "md": "markdown",
        "sql": "sql",
        "toml": "toml",
    }.get(
        suffix,
        "text",
    )

    lines = [
        f"Contents of `{path}`:",
        "",
        f"```{language}",
        content,
        "```",
    ]

    if result.get(
        "truncated",
        False,
    ):
        lines.extend(
            [
                "",
                (
                    "The displayed content was truncated "
                    f"({result.get('characters_returned', 0)} of "
                    f"{result.get('total_characters', 0)} characters)."
                ),
            ]
        )

    return "\n".join(
        lines,
    )


def _format_search_results(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "The filesystem search completed successfully."

    matches = result.get(
        "matches",
        [],
    )

    query = result.get(
        "query",
        "",
    )

    if not isinstance(
        matches,
        list,
    ) or not matches:
        return (
            f"No matches were found for `{query}` "
            f"inside `{result.get('path', '.')}`."
        )

    lines = [
        (
            f"Matches for `{query}` inside "
            f"`{result.get('path', '.')}`:"
        ),
        "",
    ]

    for match in matches:
        if not isinstance(
            match,
            dict,
        ):
            continue

        lines.append(
            "- "
            f"`{match.get('path', 'unknown')}:{match.get('line_number', '?')}` "
            f"— {match.get('excerpt', '')}"
        )

    if result.get(
        "truncated",
        False,
    ):
        lines.extend(
            [
                "",
                "The result was truncated.",
            ]
        )

    return "\n".join(
        lines,
    )


def _format_file_info(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return "File metadata was retrieved successfully."

    return "\n".join(
        [
            f"Information for `{result.get('path', 'unknown')}`:",
            "",
            f"- Type: {result.get('type', 'unknown')}",
            f"- Size: {result.get('size_bytes', 'n/a')} bytes",
            f"- Extension: {result.get('extension') or 'none'}",
            f"- Modified: {result.get('modified_at', 'unknown')}",
            f"- Read-only: {result.get('read_only', True)}",
        ]
    )


def _first_text_content(
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

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.services.unified_tool_service import (
    UnifiedToolNotFoundError,
    UnifiedToolService,
)


@dataclass(frozen=True, slots=True)
class MCPToolIntent:
    qualified_name: str
    arguments: dict[str, Any]
    matched_signal: str


FILESYSTEM_SERVER = "redpa-filesystem"

FILESYSTEM_TOOLS = {
    "list_files": (
        f"mcp:{FILESYSTEM_SERVER}:list_files"
    ),
    "read_file": (
        f"mcp:{FILESYSTEM_SERVER}:read_file"
    ),
    "search_files": (
        f"mcp:{FILESYSTEM_SERVER}:search_files"
    ),
    "file_info": (
        f"mcp:{FILESYSTEM_SERVER}:file_info"
    ),
}


async def detect_available_mcp_tool_intent(
    text: str,
) -> MCPToolIntent | None:
    """
    Detect an MCP request and verify that the selected tool exists in
    the current unified catalog before returning it to the planner.
    """

    intent = detect_mcp_tool_intent(
        text,
    )

    if intent is None:
        return None

    try:
        await UnifiedToolService.get_tool(
            qualified_name=intent.qualified_name,
        )
    except UnifiedToolNotFoundError:
        refreshed_catalog = (
            await UnifiedToolService.refresh_catalog()
        )

        if not any(
            item.qualified_name.casefold()
            == intent.qualified_name.casefold()
            for item in refreshed_catalog.items
        ):
            return None

    return intent


def detect_mcp_tool_intent(
    text: str,
) -> MCPToolIntent | None:
    cleaned_text = str(
        text
        or ""
    ).strip()

    if not cleaned_text:
        return None

    search_intent = _detect_search_intent(
        cleaned_text,
    )

    if search_intent is not None:
        return search_intent

    file_info_intent = _detect_file_info_intent(
        cleaned_text,
    )

    if file_info_intent is not None:
        return file_info_intent

    read_intent = _detect_read_intent(
        cleaned_text,
    )

    if read_intent is not None:
        return read_intent

    return _detect_list_intent(
        cleaned_text,
    )


def _detect_list_intent(
    text: str,
) -> MCPToolIntent | None:
    patterns = (
        r"\b(?:list|show|display|find)\s+"
        r"(?:me\s+)?(?:the\s+)?"
        r"(?:files|directories|folders|contents|entries)"
        r"(?:\s+(?:in|inside|under|from|of)\s+|\s+)"
        r"(?P<path>.+?)\s*[?.!]*$",
        r"\bwhat\s+(?:files|directories|folders)"
        r"\s+(?:are\s+)?(?:in|inside|under)\s+"
        r"(?P<path>.+?)\s*[?.!]*$",
        r"^\s*(?:ls|dir)\s+(?P<path>.+?)\s*$",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            continue

        path = _normalize_project_path(
            match.group(
                "path",
            )
        )

        if path is None:
            continue

        recursive = bool(
            re.search(
                r"\b(recursive|recursively|all\s+subfolders|"
                r"all\s+subdirectories)\b",
                text,
                flags=re.IGNORECASE,
            )
        )

        return MCPToolIntent(
            qualified_name=FILESYSTEM_TOOLS[
                "list_files"
            ],
            arguments={
                "path": path,
                "recursive": recursive,
                "max_entries": 100,
            },
            matched_signal="filesystem list request",
        )

    return None


def _detect_read_intent(
    text: str,
) -> MCPToolIntent | None:
    patterns = (
        r"\b(?:read|open|show|display|print)\s+"
        r"(?:me\s+)?(?:the\s+)?"
        r"(?:file\s+)?(?P<path>"
        r"(?:backend|docs)/[^\s?]+|README\.md)"
        r"\s*[?.!]*$",
        r"\b(?:content|contents)\s+of\s+"
        r"(?P<path>(?:backend|docs)/[^\s?]+|README\.md)"
        r"\s*[?.!]*$",
        r"\bwhat(?:'s|\s+is)\s+in\s+"
        r"(?P<path>(?:backend|docs)/[^\s?]+|README\.md)"
        r"\s*[?.!]*$",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            continue

        path = _normalize_project_path(
            match.group(
                "path",
            )
        )

        if path is None:
            continue

        return MCPToolIntent(
            qualified_name=FILESYSTEM_TOOLS[
                "read_file"
            ],
            arguments={
                "path": path,
                "max_characters": 20_000,
            },
            matched_signal="filesystem read request",
        )

    return None


def _detect_search_intent(
    text: str,
) -> MCPToolIntent | None:
    patterns = (
        r"\b(?:search|find)\s+(?:for\s+)?"
        r"(?:the\s+)?(?:text|string|term|code)?\s*"
        r"[\"']?(?P<query>.+?)[\"']?\s+"
        r"(?:in|inside|under|within)\s+"
        r"(?P<path>backend(?:/[^\s?]+)?|docs(?:/[^\s?]+)?)"
        r"\s*[?.!]*$",
        r"\blook\s+for\s+"
        r"(?:the\s+)?(?:text|string|term|code)?\s*"
        r"[\"']?(?P<query>.+?)[\"']?\s+"
        r"(?:in|inside|under|within)\s+"
        r"(?P<path>backend(?:/[^\s?]+)?|docs(?:/[^\s?]+)?)"
        r"\s*[?.!]*$",
        r"\bwhere\s+is\s+[\"']?(?P<query>.+?)[\"']?"
        r"\s+(?:used|defined|mentioned)\s+"
        r"(?:in|inside|under)\s+"
        r"(?P<path>backend(?:/[^\s?]+)?|docs(?:/[^\s?]+)?)"
        r"\s*[?.!]*$",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            continue

        query = str(
            match.group(
                "query",
            )
        ).strip(
            " \"'?.!"
        )

        path = _normalize_project_path(
            match.group(
                "path",
            )
        )

        if not query or path is None:
            continue

        file_pattern = (
            "*.py"
            if path.startswith(
                "backend"
            )
            else "*"
        )

        return MCPToolIntent(
            qualified_name=FILESYSTEM_TOOLS[
                "search_files"
            ],
            arguments={
                "query": query,
                "path": path,
                "file_pattern": file_pattern,
                "case_sensitive": False,
                "max_results": 50,
            },
            matched_signal="filesystem search request",
        )

    return None


def _detect_file_info_intent(
    text: str,
) -> MCPToolIntent | None:
    match = re.search(
        r"\b(?:file\s+info|file\s+information|metadata|"
        r"details|size|modified\s+time)\s+"
        r"(?:for|of|about)?\s*"
        r"(?P<path>(?:backend|docs)/[^\s?]+|README\.md)"
        r"\s*[?.!]*$",
        text,
        flags=re.IGNORECASE,
    )

    if match is None:
        return None

    path = _normalize_project_path(
        match.group(
            "path",
        )
    )

    if path is None:
        return None

    return MCPToolIntent(
        qualified_name=FILESYSTEM_TOOLS[
            "file_info"
        ],
        arguments={
            "path": path,
        },
        matched_signal="filesystem metadata request",
    )


def _normalize_project_path(
    value: str,
) -> str | None:
    path = str(
        value
        or ""
    ).strip(
        " \t\r\n\"'?.!"
    )

    path = path.replace(
        "\\",
        "/",
    )

    while path.startswith(
        "./",
    ):
        path = path[2:]

    if not path:
        return ""

    if path.casefold() == "readme.md":
        return "README.md"

    allowed_prefixes = (
        "backend",
        "docs",
    )

    if path.casefold() in allowed_prefixes:
        return path.casefold()

    for prefix in allowed_prefixes:
        prefix_with_separator = (
            prefix
            + "/"
        )

        if path.casefold().startswith(
            prefix_with_separator,
        ):
            return (
                prefix
                + path[
                    len(prefix):
                ]
            )

    return None

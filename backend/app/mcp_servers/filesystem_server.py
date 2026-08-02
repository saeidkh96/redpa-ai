from __future__ import annotations

import fnmatch
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from app.mcp_servers.filesystem_security import (
    FilesystemAccessError,
    ReadOnlyFilesystemSandbox,
    get_workspace_root,
)


SERVER_HOST = os.getenv(
    "FILESYSTEM_MCP_HOST",
    "0.0.0.0",
)

SERVER_PORT = int(
    os.getenv(
        "FILESYSTEM_MCP_PORT",
        "8010",
    )
)

sandbox = ReadOnlyFilesystemSandbox(
    get_workspace_root(),
)

mcp = MCPServer(
    "RedPA Read-Only Filesystem",
    instructions=(
        "Read-only access to selected RedPA project files. "
        "Only backend/, docs/, and README.md are exposed. "
        "Writing, deleting, command execution, hidden files, "
        "credentials, databases, and path traversal are prohibited."
    ),
)


TRANSPORT_SECURITY = TransportSecuritySettings(
    allowed_hosts=[
        "filesystem-mcp",
        "filesystem-mcp:*",
        "redpa-filesystem-mcp",
        "redpa-filesystem-mcp:*",
        "127.0.0.1",
        "127.0.0.1:*",
        "localhost",
        "localhost:*",
    ],
    allowed_origins=[],
)


@mcp.tool()
def list_files(
    path: str = "",
    recursive: bool = False,
    max_entries: int = 200,
) -> dict[str, Any]:
    """
    List visible files and directories inside the read-only sandbox.

    Args:
        path: "", backend, docs, README.md, or a child path.
        recursive: Recursively include descendants.
        max_entries: Maximum number of returned entries (1-500).
    """

    limit = max(
        1,
        min(
            int(max_entries),
            500,
        ),
    )

    target = sandbox.resolve(
        path,
    )

    if target.is_file():
        return {
            "path": sandbox.to_public_path(
                target,
            ),
            "entries": [
                _entry_metadata(
                    target,
                )
            ],
            "count": 1,
            "truncated": False,
            "read_only": True,
        }

    if target == sandbox.workspace_root:
        candidates = [
            *sandbox.allowed_roots.values(),
            *sandbox.allowed_files.values(),
        ]
    elif recursive:
        candidates = target.rglob(
            "*",
        )
    else:
        candidates = target.iterdir()

    entries: list[dict[str, Any]] = []
    truncated = False

    for candidate in candidates:
        try:
            if sandbox.should_hide(
                candidate,
            ):
                continue

            if candidate.is_symlink():
                continue

            sandbox.to_public_path(
                candidate,
            )

        except FilesystemAccessError:
            continue

        entries.append(
            _entry_metadata(
                candidate,
            )
        )

        if len(entries) >= limit:
            truncated = True
            break

    entries.sort(
        key=lambda item: (
            item["type"] != "directory",
            item["path"].casefold(),
        )
    )

    return {
        "path": (
            "."
            if target == sandbox.workspace_root
            else sandbox.to_public_path(
                target,
            )
        ),
        "entries": entries,
        "count": len(
            entries,
        ),
        "truncated": truncated,
        "read_only": True,
    }


@mcp.tool()
def read_file(
    path: str,
    max_characters: int = 20_000,
) -> dict[str, Any]:
    """
    Read a UTF-8 text file from backend/, docs/, or README.md.

    Binary files, credentials, databases, and files outside the sandbox
    are rejected.
    """

    limit = max(
        1_000,
        min(
            int(max_characters),
            100_000,
        ),
    )

    target = sandbox.resolve(
        path,
    )

    if not target.is_file():
        raise FilesystemAccessError(
            "read_file requires a regular file."
        )

    if not sandbox.is_text_file(
        target,
    ):
        raise FilesystemAccessError(
            "Only supported text files can be read."
        )

    file_size = target.stat().st_size

    if file_size > 2_000_000:
        raise FilesystemAccessError(
            "Files larger than 2 MB cannot be read."
        )

    content = target.read_text(
        encoding="utf-8",
        errors="replace",
    )

    truncated = len(
        content,
    ) > limit

    return {
        "path": sandbox.to_public_path(
            target,
        ),
        "content": content[
            :limit
        ],
        "characters_returned": min(
            len(content),
            limit,
        ),
        "total_characters": len(
            content,
        ),
        "truncated": truncated,
        "read_only": True,
    }


@mcp.tool()
def search_files(
    query: str,
    path: str = "",
    file_pattern: str = "*",
    case_sensitive: bool = False,
    max_results: int = 50,
) -> dict[str, Any]:
    """
    Search text-file contents in the read-only sandbox.

    Args:
        query: Literal text to search for.
        path: Search root inside backend/, docs/, or README.md.
        file_pattern: Filename glob such as *.py or *.md.
        case_sensitive: Enable case-sensitive matching.
        max_results: Maximum number of matches (1-200).
    """

    cleaned_query = str(
        query
        or ""
    )

    if not cleaned_query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    result_limit = max(
        1,
        min(
            int(max_results),
            200,
        ),
    )

    target = sandbox.resolve(
        path,
    )

    candidates = (
        [target]
        if target.is_file()
        else target.rglob(
            "*",
        )
    )

    normalized_query = (
        cleaned_query
        if case_sensitive
        else cleaned_query.casefold()
    )

    matches: list[dict[str, Any]] = []
    files_scanned = 0
    truncated = False

    for candidate in candidates:
        if not candidate.is_file():
            continue

        if sandbox.should_hide(
            candidate,
        ):
            continue

        if candidate.is_symlink():
            continue

        if not sandbox.is_text_file(
            candidate,
        ):
            continue

        if not fnmatch.fnmatch(
            candidate.name,
            file_pattern,
        ):
            continue

        try:
            sandbox.to_public_path(
                candidate,
            )
        except FilesystemAccessError:
            continue

        if candidate.stat().st_size > 2_000_000:
            continue

        files_scanned += 1

        try:
            lines = candidate.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()
        except OSError:
            continue

        for line_number, line in enumerate(
            lines,
            start=1,
        ):
            searchable_line = (
                line
                if case_sensitive
                else line.casefold()
            )

            if normalized_query not in searchable_line:
                continue

            excerpt = line.strip()

            if len(excerpt) > 500:
                excerpt = (
                    excerpt[:497]
                    + "..."
                )

            matches.append(
                {
                    "path": sandbox.to_public_path(
                        candidate,
                    ),
                    "line_number": line_number,
                    "excerpt": excerpt,
                }
            )

            if len(matches) >= result_limit:
                truncated = True
                break

        if truncated:
            break

    return {
        "query": cleaned_query,
        "path": (
            "."
            if target == sandbox.workspace_root
            else sandbox.to_public_path(
                target,
            )
        ),
        "file_pattern": file_pattern,
        "matches": matches,
        "match_count": len(
            matches,
        ),
        "files_scanned": files_scanned,
        "truncated": truncated,
        "read_only": True,
    }


@mcp.tool()
def file_info(
    path: str,
) -> dict[str, Any]:
    """Return safe metadata for a file or directory."""

    target = sandbox.resolve(
        path,
    )

    return _entry_metadata(
        target,
    )


def _entry_metadata(
    path: Path,
) -> dict[str, Any]:
    stat_result = path.stat()

    return {
        "path": sandbox.to_public_path(
            path,
        ),
        "name": path.name,
        "type": (
            "directory"
            if path.is_dir()
            else "file"
        ),
        "size_bytes": (
            None
            if path.is_dir()
            else stat_result.st_size
        ),
        "extension": (
            path.suffix
            if path.is_file()
            else None
        ),
        "modified_at": datetime.fromtimestamp(
            stat_result.st_mtime,
            tz=timezone.utc,
        ).isoformat(),
        "read_only": True,
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=SERVER_HOST,
        port=SERVER_PORT,
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=TRANSPORT_SECURITY,
    )

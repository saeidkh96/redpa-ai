from __future__ import annotations

import re


class MCPQualifiedNameError(ValueError):
    """Raised when a qualified MCP tool name is invalid."""


def build_mcp_qualified_name(
    *,
    server_name: str,
    tool_name: str,
) -> str:
    return (
        "mcp:"
        + _normalize_component(
            server_name,
        )
        + ":"
        + _normalize_component(
            tool_name,
        )
    )


def parse_mcp_qualified_name(
    value: str,
) -> tuple[str, str]:
    normalized = str(
        value or "",
    ).strip()

    parts = normalized.split(
        ":",
        2,
    )

    if (
        len(parts) != 3
        or parts[0].casefold() != "mcp"
        or not parts[1].strip()
        or not parts[2].strip()
    ):
        raise MCPQualifiedNameError(
            "Qualified MCP tool name must use "
            "'mcp:<server_name>:<tool_name>'."
        )

    return (
        parts[1].strip(),
        parts[2].strip(),
    )


def _normalize_component(
    value: str,
) -> str:
    normalized = re.sub(
        r"[^a-zA-Z0-9_.-]+",
        "_",
        str(
            value or "",
        ).strip().casefold(),
    ).strip("_")

    if not normalized:
        raise MCPQualifiedNameError(
            "MCP qualified-name component cannot be empty."
        )

    return normalized[:200]

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import ValidationError

from app.mcp.exceptions import MCPConfigurationError
from app.mcp.schemas import (
    MCPServerConfig,
    MCPServerListConfig,
)
from app.mcp.security import validate_remote_mcp_url


DEFAULT_CONFIG_PATH = Path(
    "config/mcp_servers.json",
)


def load_mcp_server_configs(
    config_path: str | Path | None = None,
) -> list[MCPServerConfig]:
    selected_path = Path(
        config_path
        or os.getenv(
            "MCP_SERVERS_CONFIG_PATH",
            str(
                DEFAULT_CONFIG_PATH,
            ),
        )
    )

    if not selected_path.exists():
        return []

    try:
        raw_payload = json.loads(
            selected_path.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as exception:
        raise MCPConfigurationError(
            "MCP server configuration contains invalid JSON."
        ) from exception
    except OSError as exception:
        raise MCPConfigurationError(
            "Could not read the MCP server configuration."
        ) from exception

    try:
        parsed = MCPServerListConfig.model_validate(
            raw_payload,
        )
    except ValidationError as exception:
        raise MCPConfigurationError(
            "MCP server configuration failed validation: "
            f"{exception.errors()}"
        ) from exception

    seen_names: set[str] = set()
    validated_servers: list[MCPServerConfig] = []

    for server in parsed.servers:
        normalized_name = server.name.casefold()

        if normalized_name in seen_names:
            raise MCPConfigurationError(
                f"Duplicate MCP server name '{server.name}'."
            )

        seen_names.add(
            normalized_name,
        )

        validate_remote_mcp_url(
            str(
                server.url,
            ),
            allow_private_network=(
                server.allow_private_network
            ),
        )

        validated_servers.append(
            server,
        )

    return validated_servers

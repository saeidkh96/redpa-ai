from __future__ import annotations

from app.mcp.config_loader import (
    load_mcp_server_configs,
)
from app.mcp.schemas import MCPServerConfig


class MCPServerNotFoundError(Exception):
    """Raised when an MCP server is not registered."""


class MCPServerAlreadyRegisteredError(Exception):
    """Raised when an MCP server name is registered twice."""


class MCPServerRegistry:
    """In-memory registry of configured remote MCP servers."""

    def __init__(self) -> None:
        self._servers: dict[
            str,
            MCPServerConfig,
        ] = {}

    def register(
        self,
        server: MCPServerConfig,
    ) -> None:
        name = self._normalize_name(
            server.name,
        )

        if name in self._servers:
            raise MCPServerAlreadyRegisteredError(
                f"MCP server '{name}' is already registered."
            )

        self._servers[name] = server

    def replace_all(
        self,
        servers: list[MCPServerConfig],
    ) -> None:
        new_registry: dict[
            str,
            MCPServerConfig,
        ] = {}

        for server in servers:
            name = self._normalize_name(
                server.name,
            )

            if name in new_registry:
                raise MCPServerAlreadyRegisteredError(
                    f"MCP server '{name}' is duplicated."
                )

            new_registry[name] = server

        self._servers = new_registry

    def get(
        self,
        server_name: str,
    ) -> MCPServerConfig:
        name = self._normalize_name(
            server_name,
        )

        server = self._servers.get(
            name,
        )

        if server is None:
            raise MCPServerNotFoundError(
                f"MCP server '{name}' is not registered."
            )

        return server

    def list_enabled(
        self,
    ) -> list[MCPServerConfig]:
        return sorted(
            (
                server
                for server in self._servers.values()
                if server.enabled
            ),
            key=lambda server: server.name.casefold(),
        )

    def list_all(
        self,
    ) -> list[MCPServerConfig]:
        return sorted(
            self._servers.values(),
            key=lambda server: server.name.casefold(),
        )

    def reload(
        self,
    ) -> int:
        servers = load_mcp_server_configs()
        self.replace_all(
            servers,
        )
        return len(servers)

    @staticmethod
    def _normalize_name(
        value: str,
    ) -> str:
        normalized = str(
            value,
        ).strip().casefold()

        if not normalized:
            raise ValueError(
                "MCP server name cannot be empty."
            )

        return normalized


mcp_server_registry = MCPServerRegistry()
mcp_server_registry.reload()

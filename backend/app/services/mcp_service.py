from __future__ import annotations

from typing import Any

from app.mcp.client import RedPAMCPClient
from app.mcp.registry import (
    MCPServerNotFoundError,
    mcp_server_registry,
)
from app.mcp.schemas import (
    MCPServerInfo,
    MCPToolCallResult,
    MCPToolInfo,
)


class MCPService:
    """Application service for MCP discovery and tool calls."""

    @staticmethod
    def list_servers() -> list[MCPServerInfo]:
        return [
            MCPServerInfo(
                name=server.name,
                description=server.description,
                transport=server.transport,
                url=str(server.url),
                enabled=server.enabled,
                requires_approval=server.requires_approval,
            )
            for server in mcp_server_registry.list_all()
        ]

    @staticmethod
    def reload_servers() -> int:
        return mcp_server_registry.reload()

    @staticmethod
    async def list_tools(
        *,
        server_name: str,
    ) -> list[MCPToolInfo]:
        server = mcp_server_registry.get(
            server_name,
        )

        if not server.enabled:
            return []

        return await RedPAMCPClient.list_tools(
            server,
        )

    @staticmethod
    async def call_tool(
        *,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> MCPToolCallResult:
        server = mcp_server_registry.get(
            server_name,
        )

        if not server.enabled:
            raise MCPServerNotFoundError(
                f"MCP server '{server.name}' is disabled."
            )

        return await RedPAMCPClient.call_tool(
            server=server,
            tool_name=tool_name,
            arguments=arguments,
        )

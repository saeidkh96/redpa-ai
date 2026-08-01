from __future__ import annotations

import time
from typing import Any

from app.mcp.client import RedPAMCPClient
from app.mcp.manager import MCPManager
from app.mcp.naming import (
    parse_mcp_qualified_name,
)
from app.mcp.permissions import MCPPermissionService
from app.mcp.registry import (
    MCPServerNotFoundError,
    mcp_server_registry,
)
from app.mcp.schemas import (
    MCPHealthResponse,
    MCPReloadResponse,
    MCPServerInfo,
    MCPToolCallResult,
    MCPToolCatalogResponse,
    MCPToolInfo,
)
from app.monitoring.mcp_metrics import (
    MCP_TOOL_CALL_DURATION_SECONDS,
    MCP_TOOL_CALLS_TOTAL,
)


class MCPToolNotFoundError(Exception):
    """Raised when a discovered MCP tool cannot be found."""


class MCPService:
    @staticmethod
    def list_servers() -> list[MCPServerInfo]:
        return [
            MCPServerInfo(
                name=server.name,
                description=server.description,
                transport=server.transport,
                url=str(
                    server.url,
                ),
                enabled=server.enabled,
                requires_approval=server.requires_approval,
            )
            for server in mcp_server_registry.list_all()
        ]

    @staticmethod
    async def reload_servers() -> MCPReloadResponse:
        configured_servers = (
            mcp_server_registry.reload()
        )
        await MCPManager.invalidate_cache()

        return MCPReloadResponse(
            configured_servers=configured_servers,
            message=(
                "MCP server configuration reloaded successfully."
            ),
        )

    @staticmethod
    async def health() -> MCPHealthResponse:
        return await MCPManager.health()

    @staticmethod
    async def list_all_tools(
        *,
        force_refresh: bool = False,
    ) -> MCPToolCatalogResponse:
        tools, errors, cached = (
            await MCPManager.list_all_tools(
                force_refresh=force_refresh,
            )
        )

        return MCPToolCatalogResponse(
            items=tools,
            total=len(
                tools,
            ),
            server_errors=errors,
            cached=cached,
        )

    @staticmethod
    async def get_tool(
        *,
        qualified_name: str,
    ) -> MCPToolInfo:
        server_name, tool_name = (
            parse_mcp_qualified_name(
                qualified_name,
            )
        )

        catalog = await MCPService.list_all_tools()

        for tool in catalog.items:
            if (
                tool.server_name.casefold()
                == server_name.casefold()
                and tool.name.casefold()
                == tool_name.casefold()
            ):
                return tool

        raise MCPToolNotFoundError(
            f"MCP tool '{qualified_name}' was not found."
        )

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
    async def call_qualified_tool(
        *,
        qualified_name: str,
        arguments: dict[str, Any],
        approval_granted: bool,
    ) -> MCPToolCallResult:
        server_name, tool_name = (
            parse_mcp_qualified_name(
                qualified_name,
            )
        )

        return await MCPService.call_tool(
            server_name=server_name,
            tool_name=tool_name,
            arguments=arguments,
            approval_granted=approval_granted,
        )

    @staticmethod
    async def call_tool(
        *,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        approval_granted: bool = False,
    ) -> MCPToolCallResult:
        server = mcp_server_registry.get(
            server_name,
        )

        if not server.enabled:
            raise MCPServerNotFoundError(
                f"MCP server '{server.name}' is disabled."
            )

        catalog = await MCPService.list_all_tools()

        tool = next(
            (
                candidate
                for candidate in catalog.items
                if (
                    candidate.server_name.casefold()
                    == server.name.casefold()
                    and candidate.name.casefold()
                    == tool_name.casefold()
                )
            ),
            None,
        )

        if tool is None:
            raise MCPToolNotFoundError(
                f"MCP tool '{server.name}:{tool_name}' "
                "was not found."
            )

        MCPPermissionService.enforce(
            server=server,
            tool=tool,
            approval_granted=approval_granted,
        )

        started_at = time.perf_counter()

        try:
            result = await RedPAMCPClient.call_tool(
                server=server,
                tool_name=tool.name,
                arguments=arguments,
            )

            status = (
                "success"
                if result.success
                else "error"
            )

            MCP_TOOL_CALLS_TOTAL.labels(
                server_name=server.name,
                tool_name=tool.name,
                status=status,
            ).inc()

            return result

        except Exception:
            MCP_TOOL_CALLS_TOTAL.labels(
                server_name=server.name,
                tool_name=tool.name,
                status="exception",
            ).inc()
            raise

        finally:
            MCP_TOOL_CALL_DURATION_SECONDS.labels(
                server_name=server.name,
                tool_name=tool.name,
            ).observe(
                max(
                    time.perf_counter()
                    - started_at,
                    0.0,
                )
            )

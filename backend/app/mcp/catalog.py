from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.mcp.schemas import MCPToolInfo
from app.services.mcp_service import MCPService


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MCPServerDiscoveryResult:
    server_name: str
    tools: list[MCPToolInfo]
    error: str | None


class MCPCatalog:
    """
    Discover MCP tools from every configured, enabled server.

    Discovery is isolated per server. A failing server does not make the
    complete unified catalog unavailable.
    """

    @classmethod
    async def discover_all(
        cls,
    ) -> tuple[
        list[MCPToolInfo],
        dict[str, str],
        datetime,
    ]:
        servers = [
            server
            for server in MCPService.list_servers()
            if server.enabled
        ]

        if not servers:
            return (
                [],
                {},
                datetime.now(
                    timezone.utc,
                ),
            )

        results = await asyncio.gather(
            *(
                cls._discover_server(
                    server_name=server.name,
                )
                for server in servers
            )
        )

        tools: list[MCPToolInfo] = []
        errors: dict[str, str] = {}

        for result in results:
            tools.extend(
                result.tools,
            )

            if result.error is not None:
                errors[result.server_name] = result.error

        tools.sort(
            key=lambda item: (
                item.server_name.casefold(),
                item.name.casefold(),
            )
        )

        return (
            tools,
            errors,
            datetime.now(
                timezone.utc,
            ),
        )

    @staticmethod
    async def _discover_server(
        *,
        server_name: str,
    ) -> MCPServerDiscoveryResult:
        try:
            tools = await MCPService.list_tools(
                server_name=server_name,
            )

            return MCPServerDiscoveryResult(
                server_name=server_name,
                tools=tools,
                error=None,
            )

        except Exception as exception:
            error_message = (
                f"{type(exception).__name__}: "
                f"{str(exception).strip() or 'Unknown MCP error.'}"
            )[:1000]

            logger.warning(
                "MCP tool discovery failed | server=%s error=%s",
                server_name,
                error_message,
            )

            return MCPServerDiscoveryResult(
                server_name=server_name,
                tools=[],
                error=error_message,
            )

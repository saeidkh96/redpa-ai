from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from app.mcp.cache import mcp_tool_cache
from app.mcp.client import RedPAMCPClient
from app.mcp.naming import build_mcp_qualified_name
from app.mcp.registry import mcp_server_registry
from app.mcp.schemas import (
    MCPHealthResponse,
    MCPServerHealth,
    MCPToolInfo,
)
from app.monitoring.mcp_metrics import (
    MCP_CONNECTED_SERVERS,
    MCP_DISCOVERY_CACHE_TOTAL,
    MCP_HEALTH_CHECK_DURATION_SECONDS,
    MCP_HEALTH_CHECKS_TOTAL,
)


class MCPManager:
    @classmethod
    async def health(
        cls,
    ) -> MCPHealthResponse:
        checked_at = datetime.now(
            timezone.utc,
        )
        servers = mcp_server_registry.list_all()

        if not servers:
            MCP_CONNECTED_SERVERS.set(
                0,
            )
            return MCPHealthResponse(
                status="healthy",
                configured_servers=0,
                enabled_servers=0,
                connected_servers=0,
                unavailable_servers=0,
                total_tools=0,
                checked_at=checked_at,
                servers=[],
            )

        health_results = await asyncio.gather(
            *(
                cls._check_server(
                    server_name=server.name,
                )
                for server in servers
            )
        )

        enabled_servers = sum(
            result.enabled
            for result in health_results
        )
        connected_servers = sum(
            result.status == "connected"
            for result in health_results
        )
        unavailable_servers = sum(
            result.status == "unavailable"
            for result in health_results
        )
        total_tools = sum(
            result.tool_count
            for result in health_results
        )

        MCP_CONNECTED_SERVERS.set(
            connected_servers,
        )

        status = (
            "healthy"
            if unavailable_servers == 0
            else (
                "degraded"
                if connected_servers > 0
                else "unavailable"
            )
        )

        return MCPHealthResponse(
            status=status,
            configured_servers=len(
                health_results,
            ),
            enabled_servers=enabled_servers,
            connected_servers=connected_servers,
            unavailable_servers=unavailable_servers,
            total_tools=total_tools,
            checked_at=checked_at,
            servers=health_results,
        )

    @classmethod
    async def list_all_tools(
        cls,
        *,
        force_refresh: bool = False,
    ) -> tuple[
        list[MCPToolInfo],
        dict[str, str],
        bool,
    ]:
        if not force_refresh:
            cached_entry = await mcp_tool_cache.get()

            if cached_entry is not None:
                MCP_DISCOVERY_CACHE_TOTAL.labels(
                    result="hit",
                ).inc()
                return (
                    cached_entry.tools,
                    cached_entry.server_errors,
                    True,
                )

        MCP_DISCOVERY_CACHE_TOTAL.labels(
            result="miss",
        ).inc()

        enabled_servers = (
            mcp_server_registry.list_enabled()
        )

        if not enabled_servers:
            await mcp_tool_cache.set(
                tools=[],
                server_errors={},
            )
            return (
                [],
                {},
                False,
            )

        results = await asyncio.gather(
            *(
                cls._discover_tools(
                    server_name=server.name,
                )
                for server in enabled_servers
            )
        )

        tools: list[MCPToolInfo] = []
        errors: dict[str, str] = {}

        for server_name, server_tools, error in results:
            for tool in server_tools:
                tools.append(
                    tool.model_copy(
                        update={
                            "qualified_name": (
                                build_mcp_qualified_name(
                                    server_name=server_name,
                                    tool_name=tool.name,
                                )
                            ),
                        }
                    )
                )

            if error is not None:
                errors[server_name] = error

        tools.sort(
            key=lambda item: (
                item.server_name.casefold(),
                item.name.casefold(),
            )
        )

        await mcp_tool_cache.set(
            tools=tools,
            server_errors=errors,
        )

        return (
            tools,
            errors,
            False,
        )

    @staticmethod
    async def invalidate_cache() -> None:
        await mcp_tool_cache.clear()

    @staticmethod
    async def _check_server(
        *,
        server_name: str,
    ) -> MCPServerHealth:
        server = mcp_server_registry.get(
            server_name,
        )

        if not server.enabled:
            return MCPServerHealth(
                name=server.name,
                enabled=False,
                status="disabled",
                tool_count=0,
                latency_ms=0.0,
                error=None,
                checked_at=datetime.now(
                    timezone.utc,
                ),
            )

        started_at = time.perf_counter()

        try:
            tools = await RedPAMCPClient.list_tools(
                server,
            )
            latency_seconds = max(
                time.perf_counter()
                - started_at,
                0.0,
            )
            MCP_HEALTH_CHECKS_TOTAL.labels(
                server_name=server.name,
                status="connected",
            ).inc()
            MCP_HEALTH_CHECK_DURATION_SECONDS.labels(
                server_name=server.name,
            ).observe(
                latency_seconds,
            )
            return MCPServerHealth(
                name=server.name,
                enabled=True,
                status="connected",
                tool_count=len(
                    tools,
                ),
                latency_ms=round(
                    latency_seconds * 1000,
                    2,
                ),
                error=None,
                checked_at=datetime.now(
                    timezone.utc,
                ),
            )
        except Exception as exception:
            latency_seconds = max(
                time.perf_counter()
                - started_at,
                0.0,
            )
            MCP_HEALTH_CHECKS_TOTAL.labels(
                server_name=server.name,
                status="unavailable",
            ).inc()
            MCP_HEALTH_CHECK_DURATION_SECONDS.labels(
                server_name=server.name,
            ).observe(
                latency_seconds,
            )
            return MCPServerHealth(
                name=server.name,
                enabled=True,
                status="unavailable",
                tool_count=0,
                latency_ms=round(
                    latency_seconds * 1000,
                    2,
                ),
                error=(
                    f"{type(exception).__name__}: "
                    f"{str(exception).strip() or 'Unknown MCP error.'}"
                )[:1000],
                checked_at=datetime.now(
                    timezone.utc,
                ),
            )

    @staticmethod
    async def _discover_tools(
        *,
        server_name: str,
    ) -> tuple[
        str,
        list[MCPToolInfo],
        str | None,
    ]:
        server = mcp_server_registry.get(
            server_name,
        )

        try:
            tools = await RedPAMCPClient.list_tools(
                server,
            )
            return (
                server.name,
                tools,
                None,
            )
        except Exception as exception:
            return (
                server.name,
                [],
                (
                    f"{type(exception).__name__}: "
                    f"{str(exception).strip() or 'Unknown MCP error.'}"
                )[:1000],
            )

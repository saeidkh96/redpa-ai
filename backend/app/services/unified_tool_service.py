from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any

from app.mcp.catalog import MCPCatalog
from app.monitoring.mcp_metrics import (
    MCP_DISCOVERED_TOOLS,
    MCP_DISCOVERY_DURATION_SECONDS,
    MCP_DISCOVERY_TOTAL,
    UNIFIED_TOOL_CATALOG_SIZE,
)
from app.schemas.unified_tool import (
    UnifiedToolCatalogResponse,
    UnifiedToolInfo,
)
from app.tools.registry import tool_registry


class UnifiedToolNotFoundError(Exception):
    """Raised when a qualified tool name is absent from the catalog."""


class UnifiedToolService:
    """
    Build and cache a catalog containing internal and MCP tools.

    Phase 2.1 intentionally performs discovery only. It does not change
    planner routing and does not execute MCP tools through the internal
    ToolService.
    """

    _cache: UnifiedToolCatalogResponse | None = None
    _refresh_lock = asyncio.Lock()

    @classmethod
    async def get_catalog(
        cls,
        *,
        force_refresh: bool = False,
    ) -> UnifiedToolCatalogResponse:
        if (
            cls._cache is not None
            and not force_refresh
        ):
            return cls._cache

        async with cls._refresh_lock:
            if (
                cls._cache is not None
                and not force_refresh
            ):
                return cls._cache

            catalog = await cls._build_catalog()
            cls._cache = catalog

            return catalog

    @classmethod
    async def refresh_catalog(
        cls,
    ) -> UnifiedToolCatalogResponse:
        return await cls.get_catalog(
            force_refresh=True,
        )

    @classmethod
    async def get_tool(
        cls,
        *,
        qualified_name: str,
    ) -> UnifiedToolInfo:
        normalized_name = cls._normalize_qualified_name(
            qualified_name,
        )

        catalog = await cls.get_catalog()

        for item in catalog.items:
            if (
                item.qualified_name.casefold()
                == normalized_name
            ):
                return item

        raise UnifiedToolNotFoundError(
            f"Unified tool '{qualified_name}' was not found."
        )

    @classmethod
    async def _build_catalog(
        cls,
    ) -> UnifiedToolCatalogResponse:
        internal_items = cls._build_internal_items()

        started_at = time.perf_counter()

        mcp_tools, server_errors, refreshed_at = (
            await MCPCatalog.discover_all()
        )

        discovery_duration = max(
            time.perf_counter() - started_at,
            0.0,
        )

        mcp_items = [
            UnifiedToolInfo(
                qualified_name=cls.mcp_qualified_name(
                    server_name=tool.server_name,
                    tool_name=tool.name,
                ),
                source="mcp",
                name=tool.name,
                display_name=(
                    tool.title
                    or tool.name
                ),
                description=tool.description,
                version=None,
                server_name=tool.server_name,
                requires_approval=(
                    tool.requires_approval
                ),
                input_schema=tool.input_schema,
            )
            for tool in mcp_tools
        ]

        cls._record_mcp_metrics(
            mcp_items=mcp_items,
            server_errors=server_errors,
            duration_seconds=discovery_duration,
        )

        items = [
            *internal_items,
            *mcp_items,
        ]

        items.sort(
            key=lambda item: (
                item.source,
                (
                    item.server_name
                    or ""
                ).casefold(),
                item.name.casefold(),
            )
        )

        UNIFIED_TOOL_CATALOG_SIZE.labels(
            source="internal",
        ).set(
            len(internal_items),
        )

        UNIFIED_TOOL_CATALOG_SIZE.labels(
            source="mcp",
        ).set(
            len(mcp_items),
        )

        return UnifiedToolCatalogResponse(
            items=items,
            total=len(items),
            internal_total=len(internal_items),
            mcp_total=len(mcp_items),
            mcp_server_errors=server_errors,
            refreshed_at=refreshed_at,
        )

    @staticmethod
    def _build_internal_items() -> list[UnifiedToolInfo]:
        items: list[UnifiedToolInfo] = []

        for metadata in tool_registry.list_metadata():
            metadata_data = metadata.model_dump()

            input_schema = (
                metadata_data.get(
                    "input_schema",
                )
                or metadata_data.get(
                    "parameters",
                )
                or {}
            )

            if not isinstance(
                input_schema,
                dict,
            ):
                input_schema = {}

            items.append(
                UnifiedToolInfo(
                    qualified_name=(
                        UnifiedToolService.internal_qualified_name(
                            metadata.name,
                        )
                    ),
                    source="internal",
                    name=metadata.name,
                    display_name=metadata.name,
                    description=metadata.description,
                    version=metadata.version,
                    server_name=None,
                    requires_approval=(
                        metadata.requires_approval
                    ),
                    input_schema=input_schema,
                )
            )

        return items

    @staticmethod
    def _record_mcp_metrics(
        *,
        mcp_items: list[UnifiedToolInfo],
        server_errors: dict[str, str],
        duration_seconds: float,
    ) -> None:
        counts_by_server: dict[str, int] = {}

        for item in mcp_items:
            if item.server_name is None:
                continue

            counts_by_server[item.server_name] = (
                counts_by_server.get(
                    item.server_name,
                    0,
                )
                + 1
            )

        known_servers = {
            *counts_by_server.keys(),
            *server_errors.keys(),
        }

        if not known_servers:
            return

        average_duration = (
            duration_seconds
            / max(
                len(known_servers),
                1,
            )
        )

        for server_name in known_servers:
            has_error = (
                server_name in server_errors
            )

            MCP_DISCOVERY_TOTAL.labels(
                server_name=server_name,
                status=(
                    "error"
                    if has_error
                    else "success"
                ),
            ).inc()

            MCP_DISCOVERY_DURATION_SECONDS.labels(
                server_name=server_name,
            ).observe(
                average_duration,
            )

            MCP_DISCOVERED_TOOLS.labels(
                server_name=server_name,
            ).set(
                counts_by_server.get(
                    server_name,
                    0,
                )
            )

    @staticmethod
    def internal_qualified_name(
        tool_name: str,
    ) -> str:
        return (
            "internal:"
            + UnifiedToolService._normalize_component(
                tool_name,
            )
        )

    @staticmethod
    def mcp_qualified_name(
        *,
        server_name: str,
        tool_name: str,
    ) -> str:
        return (
            "mcp:"
            + UnifiedToolService._normalize_component(
                server_name,
            )
            + ":"
            + UnifiedToolService._normalize_component(
                tool_name,
            )
        )

    @staticmethod
    def _normalize_qualified_name(
        value: str,
    ) -> str:
        normalized = str(
            value,
        ).strip().casefold()

        if not normalized:
            raise ValueError(
                "Qualified tool name cannot be empty."
            )

        return normalized

    @staticmethod
    def _normalize_component(
        value: str,
    ) -> str:
        normalized = str(
            value,
        ).strip().casefold()

        cleaned = "".join(
            character
            if (
                character.isalnum()
                or character in {
                    "_",
                    "-",
                    ".",
                }
            )
            else "_"
            for character in normalized
        ).strip("_")

        if not cleaned:
            raise ValueError(
                "Tool catalog component cannot be empty."
            )

        return cleaned[:200]

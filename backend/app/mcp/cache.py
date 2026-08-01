from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from app.mcp.schemas import MCPToolInfo


@dataclass(slots=True)
class MCPToolCacheEntry:
    tools: list[MCPToolInfo]
    server_errors: dict[str, str]
    expires_at: float


class MCPToolCache:
    """Small in-memory cache for aggregate MCP tool discovery."""

    def __init__(
        self,
        *,
        ttl_seconds: float = 30.0,
    ) -> None:
        self.ttl_seconds = max(
            1.0,
            min(
                float(ttl_seconds),
                300.0,
            ),
        )
        self._entry: MCPToolCacheEntry | None = None
        self._lock = asyncio.Lock()

    async def get(
        self,
    ) -> MCPToolCacheEntry | None:
        async with self._lock:
            if self._entry is None:
                return None

            if self._entry.expires_at <= time.monotonic():
                self._entry = None
                return None

            return MCPToolCacheEntry(
                tools=[
                    item.model_copy(
                        deep=True,
                    )
                    for item in self._entry.tools
                ],
                server_errors=dict(
                    self._entry.server_errors,
                ),
                expires_at=self._entry.expires_at,
            )

    async def set(
        self,
        *,
        tools: list[MCPToolInfo],
        server_errors: dict[str, str],
    ) -> None:
        async with self._lock:
            self._entry = MCPToolCacheEntry(
                tools=[
                    item.model_copy(
                        deep=True,
                    )
                    for item in tools
                ],
                server_errors=dict(
                    server_errors,
                ),
                expires_at=(
                    time.monotonic()
                    + self.ttl_seconds
                ),
            )

    async def clear(
        self,
    ) -> None:
        async with self._lock:
            self._entry = None


mcp_tool_cache = MCPToolCache(
    ttl_seconds=30.0,
)

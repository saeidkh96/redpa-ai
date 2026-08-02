from __future__ import annotations

import time
from typing import Any

import anyio
import httpx2
from mcp import Client
from mcp.client.streamable_http import (
    streamable_http_client,
)
from mcp.types import TextContent

from app.mcp.exceptions import (
    MCPConnectionError,
    MCPRequestError,
)
from app.mcp.schemas import (
    MCPServerConfig,
    MCPToolCallResult,
    MCPToolInfo,
)


class RedPAMCPClient:
    """
    Short-lived MCP v2 client for Streamable HTTP servers.

    MCP SDK v2 no longer accepts headers directly on Client().
    HTTP headers and timeouts are configured on an httpx2 client and
    passed through streamable_http_client().
    """

    @classmethod
    async def list_tools(
        cls,
        server: MCPServerConfig,
    ) -> list[MCPToolInfo]:
        try:
            with anyio.fail_after(
                server.timeout_seconds,
            ):
                async with cls._create_http_client(
                    server,
                ) as http_client:
                    transport = streamable_http_client(
                        str(
                            server.url,
                        ),
                        http_client=http_client,
                    )

                    async with Client(
                        transport,
                    ) as client:
                        tools: list[MCPToolInfo] = []
                        cursor: str | None = None

                        while True:
                            page = await client.list_tools(
                                cursor=cursor,
                            )

                            for tool in page.tools:
                                if (
                                    server.allowed_tools is not None
                                    and tool.name
                                    not in server.allowed_tools
                                ):
                                    continue

                                tools.append(
                                    MCPToolInfo(
                                        server_name=server.name,
                                        name=tool.name,
                                        title=getattr(
                                            tool,
                                            "title",
                                            None,
                                        ),
                                        description=tool.description,
                                        input_schema=tool.input_schema,
                                        requires_approval=(
                                            server.requires_approval
                                        ),
                                    )
                                )

                            if page.next_cursor is None:
                                break

                            cursor = page.next_cursor

                        return tools

        except TimeoutError as exception:
            raise MCPConnectionError(
                f"MCP server '{server.name}' timed out."
            ) from exception

        except MCPConnectionError:
            raise

        except Exception as exception:
            raise MCPConnectionError(
                "Could not connect to MCP server "
                f"'{server.name}': {exception}"
            ) from exception

    @classmethod
    async def call_tool(
        cls,
        *,
        server: MCPServerConfig,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> MCPToolCallResult:
        if (
            server.allowed_tools is not None
            and tool_name not in server.allowed_tools
        ):
            raise MCPRequestError(
                f"MCP tool '{tool_name}' is not allowed "
                f"for server '{server.name}'."
            )

        started_at = time.perf_counter()

        try:
            with anyio.fail_after(
                server.timeout_seconds,
            ):
                async with cls._create_http_client(
                    server,
                ) as http_client:
                    transport = streamable_http_client(
                        str(
                            server.url,
                        ),
                        http_client=http_client,
                    )

                    async with Client(
                        transport,
                    ) as client:
                        result = await client.call_tool(
                            tool_name,
                            arguments,
                        )

        except TimeoutError as exception:
            raise MCPRequestError(
                f"MCP tool '{tool_name}' timed out."
            ) from exception

        except MCPRequestError:
            raise

        except Exception as exception:
            raise MCPRequestError(
                f"MCP tool '{tool_name}' request failed: "
                f"{exception}"
            ) from exception

        content: list[dict[str, Any]] = []

        for block in result.content:
            if isinstance(
                block,
                TextContent,
            ):
                content.append(
                    {
                        "type": "text",
                        "text": block.text,
                    }
                )
                continue

            model_dump = getattr(
                block,
                "model_dump",
                None,
            )

            if callable(
                model_dump,
            ):
                content.append(
                    model_dump(
                        mode="json",
                    )
                )
            else:
                content.append(
                    {
                        "type": type(
                            block,
                        ).__name__,
                        "value": str(
                            block,
                        ),
                    }
                )

        execution_time_ms = round(
            (
                time.perf_counter()
                - started_at
            )
            * 1000,
            2,
        )

        return MCPToolCallResult(
            server_name=server.name,
            tool_name=tool_name,
            success=not result.is_error,
            is_error=result.is_error,
            content=content,
            structured_content=result.structured_content,
            execution_time_ms=execution_time_ms,
        )

    @staticmethod
    def _create_http_client(
        server: MCPServerConfig,
    ) -> httpx2.AsyncClient:
        return httpx2.AsyncClient(
            headers=(
                server.headers
                or None
            ),
            timeout=httpx2.Timeout(
                server.timeout_seconds,
            ),
            follow_redirects=True,
        )

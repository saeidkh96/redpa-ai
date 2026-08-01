from __future__ import annotations

import time
from typing import Any

import anyio
from mcp import Client
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
    Short-lived MCP client for remote Streamable HTTP servers.

    A fresh protocol client is created for each operation. This keeps
    lifecycle handling predictable in the current FastAPI deployment.
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
                async with Client(
                    str(server.url),
                    headers=server.headers or None,
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
                                and tool.name not in server.allowed_tools
                            ):
                                continue

                            tools.append(
                                MCPToolInfo(
                                    server_name=server.name,
                                    name=tool.name,
                                    title=tool.title,
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
                f"Could not connect to MCP server "
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
                async with Client(
                    str(server.url),
                    headers=server.headers or None,
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

            if callable(model_dump):
                content.append(
                    model_dump(
                        mode="json",
                    )
                )
            else:
                content.append(
                    {
                        "type": type(block).__name__,
                        "value": str(block),
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

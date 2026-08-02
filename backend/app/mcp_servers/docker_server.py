from __future__ import annotations

import os
from typing import Any

from mcp.server import MCPServer
from mcp.server.transport_security import (
    TransportSecuritySettings,
)

from app.mcp_servers.docker_client import (
    ReadOnlyDockerClient,
)


SERVER_HOST = os.getenv(
    "DOCKER_MCP_HOST",
    "0.0.0.0",
)

SERVER_PORT = int(
    os.getenv(
        "DOCKER_MCP_PORT",
        "8040",
    )
)

_client: ReadOnlyDockerClient | None = None


def get_client() -> ReadOnlyDockerClient:
    global _client

    if _client is None:
        _client = ReadOnlyDockerClient(
            timeout_seconds=float(
                os.getenv(
                    "DOCKER_MCP_TIMEOUT_SECONDS",
                    "15",
                )
            )
        )

    return _client


mcp = MCPServer(
    "RedPA Docker",
    instructions=(
        "Read-only access to Docker container listings, container "
        "metadata, logs, images, and system information. "
        "Container creation, deletion, restart, stop, exec, image "
        "mutation, volume mutation, and network mutation are not exposed."
    ),
)


TRANSPORT_SECURITY = TransportSecuritySettings(
    allowed_hosts=[
        "docker-mcp",
        "docker-mcp:*",
        "redpa-docker-mcp",
        "redpa-docker-mcp:*",
        "127.0.0.1",
        "127.0.0.1:*",
        "localhost",
        "localhost:*",
    ],
    allowed_origins=[],
)


@mcp.tool()
async def list_containers(
    all_containers: bool = True,
) -> dict[str, Any]:
    """
    List Docker containers.

    Args:
        all_containers: Include stopped containers when true.
    """

    containers = await get_client().list_containers(
        all_containers=all_containers,
    )

    return {
        "containers": containers,
        "count": len(
            containers,
        ),
        "all_containers": all_containers,
        "read_only": True,
    }


@mcp.tool()
async def inspect_container(
    container: str,
) -> dict[str, Any]:
    """
    Return safe metadata for one Docker container.

    Args:
        container: Container name or ID.
    """

    return await get_client().inspect_container(
        container,
    )


@mcp.tool()
async def container_logs(
    container: str,
    tail: int = 100,
    timestamps: bool = True,
) -> dict[str, Any]:
    """
    Return recent logs for one Docker container.

    Args:
        container: Container name or ID.
        tail: Maximum log lines, from 1 to 2000.
        timestamps: Include Docker timestamps when true.
    """

    return await get_client().container_logs(
        container,
        tail=tail,
        timestamps=timestamps,
    )


@mcp.tool()
async def list_images(
    all_images: bool = False,
) -> dict[str, Any]:
    """
    List Docker images.

    Args:
        all_images: Include intermediate images when true.
    """

    images = await get_client().list_images(
        all_images=all_images,
    )

    return {
        "images": images,
        "count": len(
            images,
        ),
        "all_images": all_images,
        "read_only": True,
    }


@mcp.tool()
async def system_info() -> dict[str, Any]:
    """Return safe Docker Engine system information."""

    return await get_client().system_info()


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=SERVER_HOST,
        port=SERVER_PORT,
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=TRANSPORT_SECURITY,
    )

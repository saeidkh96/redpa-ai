from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.mcp.exceptions import MCPConfigurationError


BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "host.docker.internal",
    "metadata.google.internal",
}


def validate_remote_mcp_url(
    url: str,
    *,
    allow_private_network: bool = False,
) -> str:
    """
    Validate an MCP Streamable HTTP endpoint.

    Public endpoints:
    - HTTPS is mandatory.
    - Private, loopback, reserved, and link-local addresses are blocked.

    Explicitly trusted internal endpoints:
    - HTTP or HTTPS is accepted.
    - Intended only for Docker-network services configured with
      allow_private_network=true.
    - Metadata and host-gateway names remain blocked.
    """

    normalized_url = str(
        url,
    ).strip()

    parsed = urlparse(
        normalized_url,
    )

    scheme = parsed.scheme.casefold()

    if allow_private_network:
        if scheme not in {
            "http",
            "https",
        }:
            raise MCPConfigurationError(
                "Trusted internal MCP URLs must use HTTP or HTTPS."
            )
    elif scheme != "https":
        raise MCPConfigurationError(
            "Remote MCP server URLs must use HTTPS."
        )

    hostname = (
        parsed.hostname
        or ""
    ).strip().casefold()

    if not hostname:
        raise MCPConfigurationError(
            "MCP server URL must contain a hostname."
        )

    if parsed.username or parsed.password:
        raise MCPConfigurationError(
            "Credentials must not be embedded in MCP URLs."
        )

    if hostname in {
        "metadata.google.internal",
        "host.docker.internal",
    }:
        raise MCPConfigurationError(
            f"MCP host '{hostname}' is blocked."
        )

    if allow_private_network:
        if hostname in {
            "localhost",
            "localhost.localdomain",
        }:
            raise MCPConfigurationError(
                "Use the Docker service name instead of localhost."
            )

        return normalized_url

    if (
        hostname in BLOCKED_HOSTNAMES
        or hostname.endswith(
            ".local",
        )
    ):
        raise MCPConfigurationError(
            f"MCP host '{hostname}' is blocked."
        )

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                hostname,
                None,
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exception:
        raise MCPConfigurationError(
            f"Could not resolve MCP host '{hostname}'."
        ) from exception

    for address in addresses:
        try:
            ip_address = ipaddress.ip_address(
                address,
            )
        except ValueError:
            continue

        if (
            ip_address.is_private
            or ip_address.is_loopback
            or ip_address.is_link_local
            or ip_address.is_multicast
            or ip_address.is_reserved
            or ip_address.is_unspecified
        ):
            raise MCPConfigurationError(
                f"MCP host '{hostname}' resolves to a blocked network."
            )

    return normalized_url

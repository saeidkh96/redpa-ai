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
) -> str:
    """
    Accept only HTTPS MCP endpoints on public networks.

    Local development endpoints are deliberately excluded from this
    first production-oriented phase.
    """

    normalized_url = str(url).strip()
    parsed = urlparse(normalized_url)

    if parsed.scheme.casefold() != "https":
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

    if (
        hostname in BLOCKED_HOSTNAMES
        or hostname.endswith(".local")
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

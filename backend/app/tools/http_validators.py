from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.tools.http_exceptions import ExternalToolValidationError


BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "host.docker.internal",
}


def validate_external_url(
    url: str,
    *,
    allowed_hosts: set[str] | None = None,
    allow_http: bool = False,
) -> str:
    cleaned_url = str(url or "").strip()

    if not cleaned_url:
        raise ExternalToolValidationError(
            "External URL cannot be empty."
        )

    parsed = urlparse(cleaned_url)

    allowed_schemes = {"https"}
    if allow_http:
        allowed_schemes.add("http")

    if parsed.scheme.casefold() not in allowed_schemes:
        raise ExternalToolValidationError(
            "External URL must use HTTPS."
        )

    hostname = (parsed.hostname or "").strip().casefold()

    if not hostname:
        raise ExternalToolValidationError(
            "External URL must contain a hostname."
        )

    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".local"):
        raise ExternalToolValidationError(
            f"Outbound requests to host '{hostname}' are blocked."
        )

    if allowed_hosts:
        normalized_allowed_hosts = {
            host.strip().casefold()
            for host in allowed_hosts
            if host and host.strip()
        }

        host_allowed = any(
            hostname == allowed_host
            or hostname.endswith(f".{allowed_host}")
            for allowed_host in normalized_allowed_hosts
        )

        if not host_allowed:
            raise ExternalToolValidationError(
                f"Host '{hostname}' is not in the tool allowlist."
            )

    _reject_private_host(hostname)

    return cleaned_url


def _reject_private_host(hostname: str) -> None:
    try:
        addresses = {
            record[4][0]
            for record in socket.getaddrinfo(
                hostname,
                None,
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exception:
        raise ExternalToolValidationError(
            f"Could not resolve external host '{hostname}'."
        ) from exception

    if not addresses:
        raise ExternalToolValidationError(
            f"External host '{hostname}' resolved to no address."
        )

    for address in addresses:
        try:
            ip_address = ipaddress.ip_address(address)
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
            raise ExternalToolValidationError(
                f"External host '{hostname}' resolved to a blocked network."
            )

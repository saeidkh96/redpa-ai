from __future__ import annotations

import re


class DockerMCPValidationError(ValueError):
    """Raised when a Docker MCP argument is invalid."""


CONTAINER_REFERENCE_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$"
)


def validate_container_reference(
    value: str,
) -> str:
    normalized = str(
        value
        or "",
    ).strip()

    normalized = normalized.removeprefix(
        "/",
    )

    if not CONTAINER_REFERENCE_PATTERN.fullmatch(
        normalized,
    ):
        raise DockerMCPValidationError(
            "Container reference must be a safe container name or ID."
        )

    return normalized


def normalize_log_tail(
    value: int,
) -> int:
    return max(
        1,
        min(
            int(value),
            2_000,
        ),
    )

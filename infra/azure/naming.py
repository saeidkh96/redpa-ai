from __future__ import annotations

import re


def normalize_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]", "-", value.lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized


def resource_name(
    project: str,
    environment: str,
    suffix: str,
    *,
    max_length: int = 63,
) -> str:
    value = normalize_name(
        f"{project}-{environment}-{suffix}",
    )
    if not value:
        raise ValueError("Generated Azure resource name is empty.")
    return value[:max_length].rstrip("-")


def acr_name(
    project: str,
    environment: str,
) -> str:
    raw = re.sub(
        r"[^a-z0-9]",
        "",
        f"{project}{environment}acr".lower(),
    )
    if len(raw) < 5:
        raw = f"{raw}redpa"
    return raw[:50]

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RedPAConfig:
    base_url: str = "http://localhost:8000"
    token: str | None = None
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "RedPAConfig":
        timeout_raw = os.getenv("REDPA_TIMEOUT_SECONDS", "30")
        try:
            timeout = float(timeout_raw)
        except ValueError as exc:
            raise ValueError("REDPA_TIMEOUT_SECONDS must be numeric.") from exc
        if timeout <= 0:
            raise ValueError("REDPA_TIMEOUT_SECONDS must be greater than zero.")

        return cls(
            base_url=os.getenv("REDPA_API_URL", "http://localhost:8000").rstrip("/"),
            token=os.getenv("REDPA_TOKEN") or None,
            timeout_seconds=timeout,
        )

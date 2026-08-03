from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class RemoteAgentAlreadyRegisteredError(RuntimeError):
    pass


class RemoteAgentNotFoundError(LookupError):
    pass


@dataclass(slots=True)
class RemoteAgentRecord:
    name: str
    base_url: str
    enabled: bool
    timeout_seconds: float
    card: Any | None = None
    connected: bool = False
    last_checked_at: datetime | None = None
    error: str | None = None


class RemoteAgentRegistry:
    def __init__(self) -> None:
        self._records: dict[str, RemoteAgentRecord] = {}
        self._lock = asyncio.Lock()

    async def register(
        self,
        record: RemoteAgentRecord,
        *,
        replace: bool = False,
    ) -> RemoteAgentRecord:
        key = record.name.casefold()

        async with self._lock:
            if key in self._records and not replace:
                raise RemoteAgentAlreadyRegisteredError(
                    f"Remote agent '{record.name}' is already registered."
                )

            self._records[key] = record

        return record

    async def get(
        self,
        name: str,
    ) -> RemoteAgentRecord:
        key = str(
            name
            or "",
        ).casefold().strip()

        record = self._records.get(
            key,
        )

        if record is None:
            raise RemoteAgentNotFoundError(
                f"Remote agent '{name}' was not found."
            )

        return record

    async def list(
        self,
    ) -> list[RemoteAgentRecord]:
        return sorted(
            self._records.values(),
            key=lambda item: item.name,
        )

    async def unregister(
        self,
        name: str,
    ) -> None:
        key = str(
            name
            or "",
        ).casefold().strip()

        async with self._lock:
            if key not in self._records:
                raise RemoteAgentNotFoundError(
                    f"Remote agent '{name}' was not found."
                )

            del self._records[key]


remote_agent_registry = RemoteAgentRegistry()

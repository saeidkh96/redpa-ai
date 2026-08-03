from __future__ import annotations

import asyncio
import os

from app.a2a_remote.client import RemoteA2AClient, RemoteA2AError
from app.a2a_remote.registry import (
    RemoteAgentNotFoundError,
    RemoteAgentRecord,
    remote_agent_registry,
)


class RemoteAgentBootstrapService:
    _initialized = False
    _lock = asyncio.Lock()

    @classmethod
    async def ensure_defaults(cls) -> None:
        if cls._initialized:
            return

        async with cls._lock:
            if cls._initialized:
                return

            enabled = os.getenv(
                "A2A_REMOTE_DEFAULT_ENABLED",
                "true",
            ).casefold() in {
                "1",
                "true",
                "yes",
                "on",
            }

            if not enabled:
                cls._initialized = True
                return

            name = os.getenv(
                "A2A_REMOTE_DEFAULT_NAME",
                "redpa-coordinator",
            ).strip()

            base_url = os.getenv(
                "A2A_REMOTE_DEFAULT_URL",
                "http://a2a-coordinator:8050",
            ).strip()

            timeout_seconds = float(
                os.getenv(
                    "A2A_REMOTE_DEFAULT_TIMEOUT_SECONDS",
                    "30",
                )
            )

            try:
                record = await remote_agent_registry.get(name)
            except RemoteAgentNotFoundError:
                record = RemoteAgentRecord(
                    name=name,
                    base_url=RemoteA2AClient.validate_base_url(
                        base_url,
                    ),
                    enabled=True,
                    timeout_seconds=max(
                        1.0,
                        min(timeout_seconds, 120.0),
                    ),
                )

                await remote_agent_registry.register(record)

            try:
                await RemoteA2AClient.resolve_card(record)
            except RemoteA2AError:
                pass

            cls._initialized = True

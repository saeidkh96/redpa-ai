from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from app.a2a_remote.client import RemoteA2AClient, RemoteA2AError
from app.a2a_remote.registry import (
    RemoteAgentNotFoundError,
    RemoteAgentRecord,
    remote_agent_registry,
)


@dataclass(frozen=True, slots=True)
class DefaultRemoteAgent:
    name: str
    base_url: str
    timeout_seconds: float = 30.0


class RemoteAgentBootstrapService:
    _initialized = False
    _lock = asyncio.Lock()

    @classmethod
    def defaults(cls) -> tuple[DefaultRemoteAgent, ...]:
        return (
            DefaultRemoteAgent("redpa-coordinator", os.getenv("A2A_COORDINATOR_URL", "http://a2a-coordinator:8050")),
            DefaultRemoteAgent("research-agent", os.getenv("RESEARCH_AGENT_URL", "http://research-agent:8061"), 60.0),
            DefaultRemoteAgent("postgres-agent", os.getenv("POSTGRES_AGENT_URL", "http://postgres-agent:8062")),
            DefaultRemoteAgent("docker-agent", os.getenv("DOCKER_AGENT_URL", "http://docker-agent:8063")),
            DefaultRemoteAgent("filesystem-agent", os.getenv("FILESYSTEM_AGENT_URL", "http://filesystem-agent:8064")),
            DefaultRemoteAgent("github-agent", os.getenv("GITHUB_AGENT_URL", "http://github-agent:8065")),
        )

    @classmethod
    async def ensure_defaults(cls) -> None:
        if cls._initialized:
            return

        async with cls._lock:
            if cls._initialized:
                return

            enabled = os.getenv("A2A_REMOTE_DEFAULT_ENABLED", "true").casefold() in {
                "1", "true", "yes", "on",
            }
            if not enabled:
                cls._initialized = True
                return

            for definition in cls.defaults():
                try:
                    record = await remote_agent_registry.get(definition.name)
                except RemoteAgentNotFoundError:
                    record = RemoteAgentRecord(
                        name=definition.name,
                        base_url=RemoteA2AClient.validate_base_url(definition.base_url),
                        enabled=True,
                        timeout_seconds=definition.timeout_seconds,
                    )
                    await remote_agent_registry.register(record)

                try:
                    await RemoteA2AClient.resolve_card(record)
                except RemoteA2AError:
                    continue

            cls._initialized = True

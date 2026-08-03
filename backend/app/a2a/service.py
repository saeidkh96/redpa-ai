from __future__ import annotations

from app.a2a.builtin_agents import (
    register_builtin_agents,
)
from app.a2a.registry import (
    AgentNotFoundError,
    agent_registry,
)
from app.a2a.schemas import (
    AgentCard,
    AgentHealthResponse,
    AgentListResponse,
    CapabilityDiscoveryResponse,
)


class AgentService:
    _initialized = False

    @classmethod
    async def ensure_initialized(
        cls,
    ) -> None:
        if cls._initialized:
            return

        await register_builtin_agents()
        cls._initialized = True

    @classmethod
    async def list_agents(
        cls,
    ) -> AgentListResponse:
        await cls.ensure_initialized()
        return await agent_registry.list()

    @classmethod
    async def get_agent(
        cls,
        agent_id: str,
    ) -> AgentCard:
        await cls.ensure_initialized()
        return await agent_registry.get(
            agent_id,
        )

    @classmethod
    async def health(
        cls,
    ) -> AgentHealthResponse:
        await cls.ensure_initialized()
        return await agent_registry.health()

    @classmethod
    async def discover(
        cls,
        query: str,
        *,
        limit: int = 10,
    ) -> CapabilityDiscoveryResponse:
        await cls.ensure_initialized()
        return await agent_registry.discover(
            query,
            limit=limit,
        )


__all__ = [
    "AgentNotFoundError",
    "AgentService",
]

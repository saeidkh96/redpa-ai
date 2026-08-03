from __future__ import annotations

from typing import Any
from uuid import UUID

from app.agent_memory.injection import (
    AgentMemoryInjectionService,
)


class AgentMemoryHooks:
    @classmethod
    async def for_planner(
        cls,
        *,
        prompt: str,
        user_id: UUID | None = None,
        workflow_id: UUID | None = None,
    ) -> dict[str, Any]:
        result = await AgentMemoryInjectionService.inject(
            prompt=prompt,
            agent_id="planner",
            user_id=user_id,
            workflow_id=workflow_id,
        )

        return {
            "prompt": result.injected_prompt,
            "memory_context": result.memory_context,
            "memory_used": result.used_memory,
        }

    @classmethod
    async def for_chat(
        cls,
        *,
        prompt: str,
        user_id: UUID | None = None,
        workflow_id: UUID | None = None,
    ) -> dict[str, Any]:
        result = await AgentMemoryInjectionService.inject(
            prompt=prompt,
            agent_id="chat",
            user_id=user_id,
            workflow_id=workflow_id,
        )

        return {
            "prompt": result.injected_prompt,
            "memory_context": result.memory_context,
            "memory_used": result.used_memory,
        }

    @classmethod
    async def for_research(
        cls,
        *,
        prompt: str,
        user_id: UUID | None = None,
        workflow_id: UUID | None = None,
    ) -> dict[str, Any]:
        result = await AgentMemoryInjectionService.inject(
            prompt=prompt,
            agent_id="research-agent",
            user_id=user_id,
            workflow_id=workflow_id,
        )

        return {
            "prompt": result.injected_prompt,
            "memory_context": result.memory_context,
            "memory_used": result.used_memory,
        }

    @classmethod
    async def for_specialist(
        cls,
        *,
        prompt: str,
        specialist_agent_id: str,
        user_id: UUID | None = None,
        workflow_id: UUID | None = None,
    ) -> dict[str, Any]:
        result = await AgentMemoryInjectionService.inject(
            prompt=prompt,
            agent_id=specialist_agent_id,
            user_id=user_id,
            workflow_id=workflow_id,
        )

        return {
            "prompt": result.injected_prompt,
            "memory_context": result.memory_context,
            "memory_used": result.used_memory,
        }

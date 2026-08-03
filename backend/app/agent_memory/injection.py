from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.agent_memory.context import (
    AgentMemoryContextBuilder,
)


@dataclass(frozen=True, slots=True)
class MemoryInjectionResult:
    original_prompt: str
    memory_context: str
    injected_prompt: str
    used_memory: bool


class AgentMemoryInjectionService:
    @classmethod
    async def inject(
        cls,
        *,
        prompt: str,
        agent_id: str,
        user_id: UUID | None = None,
        workflow_id: UUID | None = None,
        limit: int = 8,
    ) -> MemoryInjectionResult:
        memory_context = await AgentMemoryContextBuilder.build(
            query=prompt,
            agent_id=agent_id,
            user_id=user_id,
            workflow_id=workflow_id,
            limit=limit,
        )

        if not memory_context:
            return MemoryInjectionResult(
                original_prompt=prompt,
                memory_context="",
                injected_prompt=prompt,
                used_memory=False,
            )

        injected_prompt = (
            f"{memory_context}\n\n"
            "# Current Request\n\n"
            f"{prompt}"
        )

        return MemoryInjectionResult(
            original_prompt=prompt,
            memory_context=memory_context,
            injected_prompt=injected_prompt,
            used_memory=True,
        )

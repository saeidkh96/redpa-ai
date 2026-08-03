from __future__ import annotations

from collections import Counter
from typing import Any

from app.agent_memory.repository import (
    AgentMemoryRepository,
)


class AgentMemoryAnalyticsService:
    @classmethod
    async def overview(
        cls,
        *,
        limit: int = 5000,
    ) -> dict[str, Any]:
        memories = await AgentMemoryRepository.list(
            active_only=False,
            limit=limit,
        )

        scope_counts = Counter(
            memory.scope
            for memory in memories
        )

        kind_counts = Counter(
            memory.kind
            for memory in memories
        )

        agent_counts = Counter(
            memory.agent_id
            for memory in memories
        )

        embedding_counts = Counter(
            memory.embedding_status
            for memory in memories
        )

        active_count = sum(
            1
            for memory in memories
            if memory.is_active
        )

        inactive_count = (
            len(memories)
            - active_count
        )

        average_importance = (
            sum(
                memory.importance
                for memory in memories
            )
            / len(memories)
            if memories
            else 0.0
        )

        return {
            "total_memories": len(memories),
            "active_memories": active_count,
            "inactive_memories": inactive_count,
            "average_importance": round(
                average_importance,
                4,
            ),
            "by_scope": dict(scope_counts),
            "by_kind": dict(kind_counts),
            "by_agent": dict(agent_counts),
            "by_embedding_status": dict(
                embedding_counts
            ),
        }

from __future__ import annotations

from uuid import UUID

from app.agent_memory.schemas import (
    MemorySearchRequest,
)
from app.agent_memory.service import (
    AgentMemoryService,
)


class AgentMemoryContextBuilder:
    @classmethod
    async def build(
        cls,
        *,
        query: str,
        agent_id: str,
        user_id: UUID | None = None,
        workflow_id: UUID | None = None,
        limit: int = 8,
    ) -> str:
        results = await AgentMemoryService.search(
            MemorySearchRequest(
                query=query,
                agent_id=agent_id,
                user_id=user_id,
                workflow_id=workflow_id,
                scopes=[
                    "private",
                    "shared",
                    "workflow",
                    "user",
                ],
                kinds=[],
                limit=limit,
                min_score=0.2,
                include_shared=True,
            )
        )

        if not results:
            return ""

        lines = [
            "# Relevant Agent Memory",
            "",
        ]

        for index, result in enumerate(
            results,
            start=1,
        ):
            lines.extend(
                [
                    (
                        f"{index}. "
                        f"[{result.memory.scope}/"
                        f"{result.memory.kind}] "
                        f"{result.memory.content}"
                    ),
                    (
                        f"   score={result.score:.4f}; "
                        f"importance="
                        f"{result.memory.importance:.2f}"
                    ),
                    "",
                ]
            )

        return "\n".join(
            lines,
        ).strip()

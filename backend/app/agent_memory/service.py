from __future__ import annotations

from uuid import UUID

from app.agent_memory.repository import (
    AgentMemoryRepository,
    MemoryNotFoundError,
)
from app.agent_memory.schemas import (
    MemoryCreate,
    MemoryRecord,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryUpdate,
    SharedMemoryContextRequest,
    SharedMemoryPublishRequest,
)
from app.agent_memory.semantic import (
    MemorySemanticStore,
)


class AgentMemoryService:
    @classmethod
    async def create(
        cls,
        payload: MemoryCreate,
    ) -> MemoryRecord:
        memory = await AgentMemoryRepository.create(
            payload,
        )

        if payload.embed:
            try:
                await MemorySemanticStore.upsert(
                    memory,
                )

                memory = await AgentMemoryRepository.get(
                    memory.id,
                )

            except Exception:
                await AgentMemoryRepository.set_embedding_status(
                    memory.id,
                    "failed",
                )

                memory = await AgentMemoryRepository.get(
                    memory.id,
                )

        return memory

    @classmethod
    async def update(
        cls,
        memory_id: UUID,
        payload: MemoryUpdate,
    ) -> MemoryRecord:
        memory = await AgentMemoryRepository.update(
            memory_id,
            payload,
        )

        if payload.reembed:
            try:
                await MemorySemanticStore.upsert(
                    memory,
                )

                memory = await AgentMemoryRepository.get(
                    memory.id,
                )

            except Exception:
                await AgentMemoryRepository.set_embedding_status(
                    memory.id,
                    "failed",
                )

        return memory

    @classmethod
    async def delete(
        cls,
        memory_id: UUID,
    ) -> None:
        await AgentMemoryRepository.get(
            memory_id,
        )

        try:
            await MemorySemanticStore.delete(
                memory_id,
            )
        finally:
            await AgentMemoryRepository.delete(
                memory_id,
            )

    @classmethod
    async def search(
        cls,
        request: MemorySearchRequest,
    ) -> list[MemorySearchResult]:
        return await MemorySemanticStore.search(
            request,
        )

    @classmethod
    async def publish_shared(
        cls,
        payload: SharedMemoryPublishRequest,
    ) -> MemoryRecord:
        metadata = {
            **payload.metadata,
            "source_agent_id": payload.source_agent_id,
            "visible_to_agents": (
                payload.visible_to_agents
            ),
        }

        return await cls.create(
            MemoryCreate(
                agent_id=payload.source_agent_id,
                content=payload.content,
                scope="shared",
                kind=payload.kind,
                user_id=payload.user_id,
                workflow_id=payload.workflow_id,
                importance=payload.importance,
                metadata=metadata,
                embed=True,
            )
        )

    @classmethod
    async def shared_context(
        cls,
        payload: SharedMemoryContextRequest,
    ) -> list[MemorySearchResult]:
        results = await cls.search(
            MemorySearchRequest(
                query=payload.query,
                agent_id=payload.requesting_agent_id,
                user_id=payload.user_id,
                workflow_id=payload.workflow_id,
                scopes=[
                    "shared",
                    "workflow",
                    "user",
                ],
                kinds=[],
                limit=payload.limit * 2,
                min_score=payload.min_score,
                include_shared=True,
            )
        )

        visible: list[
            MemorySearchResult
        ] = []

        for result in results:
            allowed_agents = result.memory.metadata.get(
                "visible_to_agents",
                [],
            )

            if (
                not allowed_agents
                or payload.requesting_agent_id
                in allowed_agents
                or "*"
                in allowed_agents
            ):
                visible.append(
                    result,
                )

        return visible[: payload.limit]

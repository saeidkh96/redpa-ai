from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Any
from uuid import UUID

import httpx

from app.agent_memory.repository import (
    AgentMemoryRepository,
)
from app.agent_memory.schemas import (
    MemoryRecord,
    MemorySearchRequest,
    MemorySearchResult,
)


class MemorySemanticStore:
    COLLECTION = os.getenv(
        "MEMORY_QDRANT_COLLECTION",
        "redpa_agent_memories",
    )

    VECTOR_SIZE = int(
        os.getenv(
            "MEMORY_VECTOR_SIZE",
            "384",
        )
    )

    @classmethod
    async def ensure_collection(cls) -> None:
        base_url = os.getenv(
            "QDRANT_URL",
            "http://qdrant:6333",
        ).rstrip("/")

        async with httpx.AsyncClient(
            timeout=20.0,
        ) as client:
            response = await client.get(
                f"{base_url}/collections/{cls.COLLECTION}"
            )

            if response.status_code == 200:
                return

            create_response = await client.put(
                f"{base_url}/collections/{cls.COLLECTION}",
                json={
                    "vectors": {
                        "size": cls.VECTOR_SIZE,
                        "distance": "Cosine",
                    }
                },
            )

            create_response.raise_for_status()

    @classmethod
    async def upsert(
        cls,
        memory: MemoryRecord,
    ) -> None:
        await cls.ensure_collection()

        base_url = os.getenv(
            "QDRANT_URL",
            "http://qdrant:6333",
        ).rstrip("/")

        vector = cls.embed_text(
            memory.content,
        )

        payload = {
            "memory_id": str(
                memory.id,
            ),
            "agent_id": memory.agent_id,
            "scope": memory.scope,
            "kind": memory.kind,
            "user_id": (
                str(
                    memory.user_id,
                )
                if memory.user_id
                else None
            ),
            "workflow_id": (
                str(
                    memory.workflow_id,
                )
                if memory.workflow_id
                else None
            ),
            "importance": memory.importance,
            "is_active": memory.is_active,
            "created_at": memory.created_at.isoformat(),
            "metadata": memory.metadata,
        }

        async with httpx.AsyncClient(
            timeout=20.0,
        ) as client:
            response = await client.put(
                (
                    f"{base_url}/collections/"
                    f"{cls.COLLECTION}/points"
                ),
                params={
                    "wait": "true",
                },
                json={
                    "points": [
                        {
                            "id": str(
                                memory.id,
                            ),
                            "vector": vector,
                            "payload": payload,
                        }
                    ]
                },
            )

            response.raise_for_status()

        await AgentMemoryRepository.set_embedding_status(
            memory.id,
            "ready",
        )

    @classmethod
    async def delete(
        cls,
        memory_id: UUID,
    ) -> None:
        await cls.ensure_collection()

        base_url = os.getenv(
            "QDRANT_URL",
            "http://qdrant:6333",
        ).rstrip("/")

        async with httpx.AsyncClient(
            timeout=20.0,
        ) as client:
            response = await client.post(
                (
                    f"{base_url}/collections/"
                    f"{cls.COLLECTION}/points/delete"
                ),
                params={
                    "wait": "true",
                },
                json={
                    "points": [
                        str(
                            memory_id,
                        )
                    ]
                },
            )

            response.raise_for_status()

    @classmethod
    async def search(
        cls,
        request: MemorySearchRequest,
    ) -> list[MemorySearchResult]:
        await cls.ensure_collection()

        base_url = os.getenv(
            "QDRANT_URL",
            "http://qdrant:6333",
        ).rstrip("/")

        filters = cls._build_filter(
            request,
        )

        body: dict[str, Any] = {
            "vector": cls.embed_text(
                request.query,
            ),
            "limit": request.limit * 3,
            "with_payload": True,
            "score_threshold": request.min_score,
        }

        if filters:
            body["filter"] = filters

        async with httpx.AsyncClient(
            timeout=20.0,
        ) as client:
            response = await client.post(
                (
                    f"{base_url}/collections/"
                    f"{cls.COLLECTION}/points/search"
                ),
                json=body,
            )

            response.raise_for_status()
            points = response.json().get(
                "result",
                [],
            )

        results: list[
            MemorySearchResult
        ] = []

        memory_ids: list[UUID] = []

        for point in points:
            payload = point.get(
                "payload",
                {},
            )

            memory_id_raw = payload.get(
                "memory_id",
            )

            if not memory_id_raw:
                continue

            memory_id = UUID(
                memory_id_raw,
            )

            try:
                memory = await AgentMemoryRepository.get(
                    memory_id,
                )
            except Exception:
                continue

            semantic_score = float(
                point.get(
                    "score",
                    0.0,
                )
            )

            importance_score = float(
                memory.importance,
            )

            recency_score = cls._recency_score(
                memory,
            )

            combined_score = (
                semantic_score * 0.70
                + importance_score * 0.20
                + recency_score * 0.10
            )

            results.append(
                MemorySearchResult(
                    memory=memory,
                    score=round(
                        combined_score,
                        4,
                    ),
                    semantic_score=round(
                        semantic_score,
                        4,
                    ),
                    importance_score=round(
                        importance_score,
                        4,
                    ),
                    recency_score=round(
                        recency_score,
                        4,
                    ),
                )
            )

            memory_ids.append(
                memory_id,
            )

        results.sort(
            key=lambda item: (
                -item.score,
                -item.memory.importance,
                item.memory.created_at,
            )
        )

        await AgentMemoryRepository.touch(
            memory_ids,
        )

        return results[: request.limit]

    @classmethod
    def _build_filter(
        cls,
        request: MemorySearchRequest,
    ) -> dict[str, Any] | None:
        must: list[
            dict[str, Any]
        ] = [
            {
                "key": "is_active",
                "match": {
                    "value": True,
                },
            }
        ]

        if request.user_id is not None:
            must.append(
                {
                    "key": "user_id",
                    "match": {
                        "value": str(
                            request.user_id,
                        ),
                    },
                }
            )

        if request.workflow_id is not None:
            must.append(
                {
                    "key": "workflow_id",
                    "match": {
                        "value": str(
                            request.workflow_id,
                        ),
                    },
                }
            )

        if request.kinds:
            must.append(
                {
                    "key": "kind",
                    "match": {
                        "any": request.kinds,
                    },
                }
            )

        should: list[
            dict[str, Any]
        ] = []

        if request.agent_id:
            should.append(
                {
                    "key": "agent_id",
                    "match": {
                        "value": request.agent_id,
                    },
                }
            )

        allowed_scopes = list(
            request.scopes,
        )

        if not request.include_shared:
            allowed_scopes = [
                scope
                for scope in allowed_scopes
                if scope != "shared"
            ]

        if allowed_scopes:
            must.append(
                {
                    "key": "scope",
                    "match": {
                        "any": allowed_scopes,
                    },
                }
            )

        result: dict[
            str,
            Any,
        ] = {
            "must": must,
        }

        if should:
            result["should"] = should

        return result

    @classmethod
    def embed_text(
        cls,
        text: str,
    ) -> list[float]:
        tokens = re.findall(
            r"[A-Za-z0-9_]{2,}",
            str(
                text
                or "",
            ).casefold(),
        )

        vector = [
            0.0
            for _ in range(
                cls.VECTOR_SIZE,
            )
        ]

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(
                token.encode(
                    "utf-8",
                )
            ).digest()

            index = int.from_bytes(
                digest[:4],
                "big",
            ) % cls.VECTOR_SIZE

            sign = (
                1.0
                if digest[4] % 2 == 0
                else -1.0
            )

            weight = 1.0 + (
                digest[5] / 255.0
            )

            vector[index] += (
                sign
                * weight
            )

        norm = math.sqrt(
            sum(
                value * value
                for value in vector
            )
        )

        if norm == 0.0:
            return vector

        return [
            value / norm
            for value in vector
        ]

    @staticmethod
    def _recency_score(
        memory: MemoryRecord,
    ) -> float:
        from datetime import (
            datetime,
            timezone,
        )

        age_seconds = max(
            (
                datetime.now(
                    timezone.utc,
                )
                - memory.created_at
            ).total_seconds(),
            0.0,
        )

        age_days = (
            age_seconds
            / 86_400.0
        )

        return 1.0 / (
            1.0
            + age_days / 30.0
        )

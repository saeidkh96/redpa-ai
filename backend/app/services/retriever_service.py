from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    score: float
    content_id: str | None = None
    user_id: str | None = None
    conversation_id: str | None = None
    metadata: dict[str, Any] | None = None


class RetrieverServiceError(Exception):
    """Raised when semantic document retrieval fails."""


class RetrieverService:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStoreService | None = None,
        default_limit: int = 5,
        default_score_threshold: float | None = 0.50,
    ) -> None:
        self.embedding_service = (
            embedding_service or EmbeddingService()
        )

        self.vector_store = (
            vector_store or VectorStoreService()
        )

        self.default_limit = default_limit
        self.default_score_threshold = (
            default_score_threshold
        )

    async def retrieve(
        self,
        *,
        query: str,
        limit: int | None = None,
        score_threshold: float | None = None,
        document_id: UUID | str | None = None,
        user_id: UUID | str | None = None,
        conversation_id: UUID | str | None = None,
    ) -> list[RetrievedChunk]:
        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError(
                "Retrieval query cannot be empty."
            )

        search_limit = (
            limit
            if limit is not None
            else self.default_limit
        )

        if search_limit < 1:
            raise ValueError(
                "Retrieval limit must be at least 1."
            )

        resolved_score_threshold = (
            score_threshold
            if score_threshold is not None
            else self.default_score_threshold
        )

        try:
            await self.vector_store.initialize()

            query_embedding = (
                await self.embedding_service.embed_text(
                    cleaned_query
                )
            )

            search_results = (
                await self.vector_store.search(
                    embedding=query_embedding,
                    limit=search_limit,
                    score_threshold=(
                        resolved_score_threshold
                    ),
                    document_id=document_id,
                    user_id=user_id,
                    conversation_id=conversation_id,
                )
            )

        except Exception as exc:
            raise RetrieverServiceError(
                f"Document retrieval failed: {exc}"
            ) from exc

        retrieved_chunks: list[RetrievedChunk] = []

        for result in search_results:
            payload = result.payload or {}

            text = str(
                payload.get("text", "")
            ).strip()

            if not text:
                continue

            metadata = payload.get("metadata")

            if not isinstance(metadata, dict):
                metadata = None

            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=str(
                        payload.get(
                            "chunk_id",
                            result.id,
                        )
                    ),
                    document_id=str(
                        payload.get(
                            "document_id",
                            "",
                        )
                    ),
                    content_id=self._optional_string(
                        payload.get("content_id")
                    ),
                    user_id=self._optional_string(
                        payload.get("user_id")
                    ),
                    conversation_id=(
                        self._optional_string(
                            payload.get(
                                "conversation_id"
                            )
                        )
                    ),
                    chunk_index=int(
                        payload.get(
                            "chunk_index",
                            0,
                        )
                    ),
                    text=text,
                    score=float(result.score),
                    metadata=metadata,
                )
            )

        return retrieved_chunks

    async def retrieve_for_user(
        self,
        *,
        query: str,
        user_id: UUID,
        limit: int | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        return await self.retrieve(
            query=query,
            user_id=user_id,
            limit=limit,
            score_threshold=score_threshold,
        )

    async def retrieve_for_conversation(
        self,
        *,
        query: str,
        user_id: UUID,
        conversation_id: UUID,
        limit: int | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        return await self.retrieve(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            limit=limit,
            score_threshold=score_threshold,
        )

    async def retrieve_from_document(
        self,
        *,
        query: str,
        user_id: UUID,
        document_id: UUID,
        limit: int | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        return await self.retrieve(
            query=query,
            user_id=user_id,
            document_id=document_id,
            limit=limit,
            score_threshold=score_threshold,
        )

    async def close(self) -> None:
        await self.vector_store.close()

        close_method = getattr(
            self.embedding_service,
            "close",
            None,
        )

        if close_method is not None:
            await close_method()

    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        return str(value)
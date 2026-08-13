from __future__ import annotations

from typing import Any
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
)


class VectorStoreServiceError(Exception):
    """Raised when an operation on Qdrant fails."""


class VectorStoreService:
    COLLECTION_NAME = "documents"
    VECTOR_SIZE = 768

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.collection_name = (
            collection_name or self.COLLECTION_NAME
        )

        self.client = AsyncQdrantClient(url=self.url)

    async def initialize(self) -> None:
        """
        Create the Qdrant collection when it does not exist.
        """
        try:
            collection_exists = await self.client.collection_exists(
                collection_name=self.collection_name
            )

            if collection_exists:
                return

            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

        except Exception as exc:
            raise VectorStoreServiceError(
                f"Could not initialize Qdrant collection "
                f"'{self.collection_name}': {exc}"
            ) from exc

    async def add_chunk(
        self,
        *,
        chunk_id: str | UUID,
        document_id: str | UUID,
        chunk_index: int,
        text: str,
        embedding: list[float],
        content_id: str | UUID | None = None,
        user_id: str | UUID | None = None,
        conversation_id: str | UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Store or update one document chunk in Qdrant.
        """
        self._validate_embedding(embedding)

        cleaned_text = text.strip()

        if not cleaned_text:
            raise ValueError("Chunk text cannot be empty.")

        payload: dict[str, Any] = {
            "chunk_id": str(chunk_id),
            "document_id": str(document_id),
            "chunk_index": chunk_index,
            "text": cleaned_text,
        }

        if content_id is not None:
            payload["content_id"] = str(content_id)

        if user_id is not None:
            payload["user_id"] = str(user_id)

        if conversation_id is not None:
            payload["conversation_id"] = str(conversation_id)

        if metadata:
            payload["metadata"] = metadata

        point = PointStruct(
            id=str(chunk_id),
            vector=embedding,
            payload=payload,
        )

        try:
            await self.client.upsert(
                collection_name=self.collection_name,
                wait=True,
                points=[point],
            )

        except Exception as exc:
            raise VectorStoreServiceError(
                f"Could not store chunk '{chunk_id}' "
                f"in Qdrant: {exc}"
            ) from exc

    async def add_chunks(
        self,
        chunks: list[dict[str, Any]],
    ) -> int:
        """
        Store multiple chunks in a single Qdrant request.

        Each item must contain:
        - chunk_id
        - document_id
        - chunk_index
        - text
        - embedding
        """
        if not chunks:
            return 0

        points: list[PointStruct] = []

        for chunk in chunks:
            embedding = chunk.get("embedding")
            text = str(chunk.get("text", "")).strip()

            if not isinstance(embedding, list):
                raise ValueError(
                    "Every chunk must contain an embedding list."
                )

            self._validate_embedding(embedding)

            if not text:
                raise ValueError(
                    "Every chunk must contain non-empty text."
                )

            chunk_id = chunk.get("chunk_id")
            document_id = chunk.get("document_id")

            if chunk_id is None:
                raise ValueError(
                    "Every chunk must contain chunk_id."
                )

            if document_id is None:
                raise ValueError(
                    "Every chunk must contain document_id."
                )

            payload: dict[str, Any] = {
                "chunk_id": str(chunk_id),
                "document_id": str(document_id),
                "chunk_index": int(
                    chunk.get("chunk_index", 0)
                ),
                "text": text,
            }

            optional_fields = (
                "content_id",
                "user_id",
                "conversation_id",
            )

            for field_name in optional_fields:
                field_value = chunk.get(field_name)

                if field_value is not None:
                    payload[field_name] = str(field_value)

            metadata = chunk.get("metadata")

            if isinstance(metadata, dict) and metadata:
                payload["metadata"] = metadata

            points.append(
                PointStruct(
                    id=str(chunk_id),
                    vector=embedding,
                    payload=payload,
                )
            )

        try:
            await self.client.upsert(
                collection_name=self.collection_name,
                wait=True,
                points=points,
            )

        except Exception as exc:
            raise VectorStoreServiceError(
                f"Could not store chunks in Qdrant: {exc}"
            ) from exc

        return len(points)

    async def search(
        self,
        embedding: list[float],
        limit: int = 5,
        score_threshold: float | None = None,
        document_id: str | UUID | None = None,
        user_id: str | UUID | None = None,
        conversation_id: str | UUID | None = None,
    ) -> list[Any]:
        """
        Search for chunks semantically similar to the query vector.
        """
        self._validate_embedding(embedding)

        if limit < 1:
            raise ValueError("Search limit must be at least 1.")

        query_filter = self._build_filter(
            document_id=document_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        try:
            response = await self.client.query_points(
                collection_name=self.collection_name,
                query=embedding,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False,
            )

        except Exception as exc:
            raise VectorStoreServiceError(
                f"Could not search Qdrant collection "
                f"'{self.collection_name}': {exc}"
            ) from exc

        return response.points

    async def delete_document(
        self,
        document_id: str | UUID,
    ) -> None:
        """
        Delete all vectors belonging to one document.
        """
        document_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(
                        value=str(document_id)
                    ),
                )
            ]
        )

        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=document_filter,
                wait=True,
            )

        except Exception as exc:
            raise VectorStoreServiceError(
                f"Could not delete vectors for document "
                f"'{document_id}': {exc}"
            ) from exc

    async def health_check(self) -> dict[str, Any]:
        """
        Check Qdrant connectivity and collection availability.
        """
        try:
            collections = await self.client.get_collections()

            collection_names = [
                collection.name
                for collection in collections.collections
            ]

            return {
                "available": True,
                "url": self.url,
                "collection": self.collection_name,
                "collection_exists": (
                    self.collection_name in collection_names
                ),
                "collections": collection_names,
            }

        except Exception as exc:
            return {
                "available": False,
                "url": self.url,
                "collection": self.collection_name,
                "error": str(exc),
            }

    async def close(self) -> None:
        """
        Close the asynchronous Qdrant client.
        """
        await self.client.close()

    def _validate_embedding(
        self,
        embedding: list[float],
    ) -> None:
        if not embedding:
            raise ValueError(
                "Embedding vector cannot be empty."
            )

        if len(embedding) != self.VECTOR_SIZE:
            raise ValueError(
                f"Embedding dimension must be "
                f"{self.VECTOR_SIZE}, but received "
                f"{len(embedding)}."
            )

        if not all(
            isinstance(value, int | float)
            for value in embedding
        ):
            raise ValueError(
                "Embedding must contain only numeric values."
            )

    @staticmethod
    def _build_filter(
        *,
        document_id: str | UUID | None = None,
        user_id: str | UUID | None = None,
        conversation_id: str | UUID | None = None,
    ) -> Filter | None:
        conditions: list[FieldCondition] = []

        filter_values = {
            "document_id": document_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
        }

        for field_name, field_value in filter_values.items():
            if field_value is not None:
                conditions.append(
                    FieldCondition(
                        key=field_name,
                        match=MatchValue(
                            value=str(field_value)
                        ),
                    )
                )

        if not conditions:
            return None

        return Filter(must=conditions)
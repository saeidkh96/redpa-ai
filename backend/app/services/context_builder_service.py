from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from app.services.retriever_service import RetrievedChunk


@dataclass(slots=True)
class ContextSource:
    source_number: int
    chunk_id: str
    document_id: str
    chunk_index: int
    score: float
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BuiltContext:
    context: str
    sources: list[ContextSource]
    total_characters: int
    truncated: bool


class ContextBuilderError(Exception):
    """Raised when retrieved chunks cannot be converted into RAG context."""


class ContextBuilderService:
    def __init__(
        self,
        *,
        max_characters: int = 12_000,
        separator: str = "\n\n",
        include_source_headers: bool = True,
    ) -> None:
        if max_characters < 1:
            raise ValueError(
                "max_characters must be greater than zero."
            )

        self.max_characters = max_characters
        self.separator = separator
        self.include_source_headers = include_source_headers

    def build(
        self,
        chunks: Iterable[RetrievedChunk],
        *,
        max_characters: int | None = None,
    ) -> BuiltContext:
        resolved_max_characters = (
            max_characters
            if max_characters is not None
            else self.max_characters
        )

        if resolved_max_characters < 1:
            raise ValueError(
                "max_characters must be greater than zero."
            )

        normalized_chunks = self._normalize_chunks(chunks)

        if not normalized_chunks:
            return BuiltContext(
                context="",
                sources=[],
                total_characters=0,
                truncated=False,
            )

        context_parts: list[str] = []
        sources: list[ContextSource] = []
        current_length = 0
        truncated = False

        for source_number, chunk in enumerate(
            normalized_chunks,
            start=1,
        ):
            source = ContextSource(
                source_number=source_number,
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                score=chunk.score,
                text=chunk.text,
                metadata=chunk.metadata or {},
            )

            formatted_chunk = self._format_source(source)

            separator_length = (
                len(self.separator)
                if context_parts
                else 0
            )

            available_characters = (
                resolved_max_characters
                - current_length
                - separator_length
            )

            if available_characters <= 0:
                truncated = True
                break

            if len(formatted_chunk) > available_characters:
                shortened_chunk = self._truncate_text(
                    formatted_chunk,
                    available_characters,
                )

                if shortened_chunk:
                    context_parts.append(shortened_chunk)
                    sources.append(source)
                    current_length += (
                        separator_length
                        + len(shortened_chunk)
                    )

                truncated = True
                break

            context_parts.append(formatted_chunk)
            sources.append(source)
            current_length += (
                separator_length
                + len(formatted_chunk)
            )

        context = self.separator.join(context_parts)

        return BuiltContext(
            context=context,
            sources=sources,
            total_characters=len(context),
            truncated=truncated,
        )

    def _normalize_chunks(
        self,
        chunks: Iterable[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        unique_chunks: dict[str, RetrievedChunk] = {}

        for chunk in chunks:
            text = chunk.text.strip()

            if not text:
                continue

            deduplication_key = self._build_deduplication_key(
                chunk
            )

            existing_chunk = unique_chunks.get(
                deduplication_key
            )

            if (
                existing_chunk is None
                or chunk.score > existing_chunk.score
            ):
                unique_chunks[deduplication_key] = chunk

        return sorted(
            unique_chunks.values(),
            key=lambda item: item.score,
            reverse=True,
        )

    def _format_source(
        self,
        source: ContextSource,
    ) -> str:
        if not self.include_source_headers:
            return source.text.strip()

        return (
            f"[Source {source.source_number}]\n"
            f"Document ID: {source.document_id}\n"
            f"Chunk: {source.chunk_index}\n"
            f"Relevance Score: {source.score:.4f}\n"
            f"Content:\n{source.text.strip()}"
        )

    @staticmethod
    def _build_deduplication_key(
        chunk: RetrievedChunk,
    ) -> str:
        normalized_text = " ".join(
            chunk.text.lower().split()
        )

        return (
            f"{chunk.document_id}:"
            f"{chunk.chunk_index}:"
            f"{normalized_text}"
        )

    @staticmethod
    def _truncate_text(
        text: str,
        max_length: int,
    ) -> str:
        if max_length <= 0:
            return ""

        if len(text) <= max_length:
            return text

        truncation_suffix = "\n[Context truncated]"

        if max_length <= len(truncation_suffix):
            return text[:max_length]

        shortened_text = text[
            : max_length - len(truncation_suffix)
        ].rstrip()

        return f"{shortened_text}{truncation_suffix}"
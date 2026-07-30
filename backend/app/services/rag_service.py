from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.prompts.rag_prompt import (
    RAG_PROMPT_TEMPLATE,
    RAG_SYSTEM_PROMPT,
)
from app.schemas.ollama import OllamaChatMessage
from app.services.context_builder_service import (
    BuiltContext,
    ContextBuilderService,
)
from app.services.llm_service import (
    LLMService,
    llm_service,
)
from app.services.retriever_service import (
    RetrievedChunk,
    RetrieverService,
)


@dataclass(slots=True)
class RAGSource:
    source_number: int
    document_id: str
    chunk_id: str
    chunk_index: int
    score: float
    text: str
    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass(slots=True)
class RAGResult:
    answer: str
    model: str
    provider: str
    context_used: bool
    sources: list[RAGSource]
    retrieval_count: int
    context_characters: int
    context_truncated: bool
    usage: dict[str, Any] = field(
        default_factory=dict,
    )


class RAGServiceError(Exception):
    """Raised when the RAG workflow cannot complete."""


class RAGService:
    def __init__(
        self,
        *,
        retriever: RetrieverService | None = None,
        context_builder: ContextBuilderService | None = None,
        language_model_service: LLMService | None = None,
        default_limit: int = 5,
        default_score_threshold: float = 0.20,
        default_max_context_characters: int = 12_000,
    ) -> None:
        if default_limit < 1:
            raise ValueError(
                "default_limit must be at least 1."
            )

        if default_max_context_characters < 1:
            raise ValueError(
                "default_max_context_characters must be greater "
                "than zero."
            )

        self.retriever = retriever or RetrieverService(
            default_limit=default_limit,
            default_score_threshold=default_score_threshold,
        )

        self.context_builder = (
            context_builder
            or ContextBuilderService(
                max_characters=(
                    default_max_context_characters
                ),
                include_source_headers=True,
            )
        )

        self.llm_service = (
            language_model_service
            or llm_service
        )

        self.default_limit = default_limit

        self.default_score_threshold = (
            default_score_threshold
        )

        self.default_max_context_characters = (
            default_max_context_characters
        )

    async def answer(
        self,
        *,
        question: str,
        user_id: UUID,
        conversation_id: UUID | None = None,
        document_id: UUID | None = None,
        limit: int | None = None,
        score_threshold: float | None = None,
        max_context_characters: int | None = None,
    ) -> RAGResult:
        cleaned_question = question.strip()

        if not cleaned_question:
            raise ValueError(
                "RAG question cannot be empty."
            )

        resolved_limit = (
            limit
            if limit is not None
            else self.default_limit
        )

        resolved_score_threshold = (
            score_threshold
            if score_threshold is not None
            else self.default_score_threshold
        )

        resolved_max_context_characters = (
            max_context_characters
            if max_context_characters is not None
            else self.default_max_context_characters
        )

        if resolved_limit < 1:
            raise ValueError(
                "Retrieval limit must be at least 1."
            )

        if resolved_max_context_characters < 1:
            raise ValueError(
                "Maximum context characters must be greater "
                "than zero."
            )

        try:
            retrieved_chunks = await self._retrieve_chunks(
                question=cleaned_question,
                user_id=user_id,
                conversation_id=conversation_id,
                document_id=document_id,
                limit=resolved_limit,
                score_threshold=resolved_score_threshold,
            )

            built_context = self.context_builder.build(
                retrieved_chunks,
                max_characters=(
                    resolved_max_context_characters
                ),
            )

            if not built_context.context.strip():
                return self._build_no_context_result()

            llm_messages = self._build_messages(
                question=cleaned_question,
                built_context=built_context,
            )

            llm_response = await self.llm_service.generate(
                messages=llm_messages,
            )

            answer = (
                llm_response.message.content.strip()
            )

            if not answer:
                raise RAGServiceError(
                    "The language model returned an empty "
                    "RAG response."
                )

            sources = self._build_sources(
                chunks=retrieved_chunks,
                built_context=built_context,
            )

            return RAGResult(
                answer=answer,
                model=llm_response.model,
                provider="ollama",
                context_used=True,
                sources=sources,
                retrieval_count=len(
                    retrieved_chunks
                ),
                context_characters=(
                    built_context.total_characters
                ),
                context_truncated=(
                    built_context.truncated
                ),
                usage={
                    "prompt_eval_count": (
                        llm_response.prompt_eval_count
                    ),
                    "eval_count": (
                        llm_response.eval_count
                    ),
                    "total_duration": (
                        llm_response.total_duration
                    ),
                    "load_duration": (
                        llm_response.load_duration
                    ),
                    "prompt_eval_duration": (
                        llm_response.prompt_eval_duration
                    ),
                    "eval_duration": (
                        llm_response.eval_duration
                    ),
                },
            )

        except RAGServiceError:
            raise

        except LLMServiceError:
            raise

        except Exception as exception:
            raise RAGServiceError(
                f"The RAG workflow failed: {exception}"
            ) from exception

    async def _retrieve_chunks(
        self,
        *,
        question: str,
        user_id: UUID,
        conversation_id: UUID | None,
        document_id: UUID | None,
        limit: int,
        score_threshold: float,
    ) -> list[RetrievedChunk]:
        if document_id is not None:
            return await self.retriever.retrieve_from_document(
                query=question,
                user_id=user_id,
                document_id=document_id,
                limit=limit,
                score_threshold=score_threshold,
            )

        if conversation_id is not None:
            return (
                await self.retriever.retrieve_for_conversation(
                    query=question,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    limit=limit,
                    score_threshold=score_threshold,
                )
            )

        return await self.retriever.retrieve_for_user(
            query=question,
            user_id=user_id,
            limit=limit,
            score_threshold=score_threshold,
        )

    def _build_messages(
        self,
        *,
        question: str,
        built_context: BuiltContext,
    ) -> list[OllamaChatMessage]:
        user_prompt = RAG_PROMPT_TEMPLATE.format(
            context=built_context.context,
            question=question,
        ).strip()

        return [
            OllamaChatMessage(
                role="system",
                content=RAG_SYSTEM_PROMPT.strip(),
            ),
            OllamaChatMessage(
                role="user",
                content=user_prompt,
            ),
        ]

    @staticmethod
    def _build_sources(
        *,
        chunks: list[RetrievedChunk],
        built_context: BuiltContext,
    ) -> list[RAGSource]:
        chunks_by_id = {
            chunk.chunk_id: chunk
            for chunk in chunks
        }

        sources: list[RAGSource] = []

        for context_source in built_context.sources:
            retrieved_chunk = chunks_by_id.get(
                context_source.chunk_id
            )

            if retrieved_chunk is None:
                continue

            sources.append(
                RAGSource(
                    source_number=(
                        context_source.source_number
                    ),
                    document_id=(
                        retrieved_chunk.document_id
                    ),
                    chunk_id=(
                        retrieved_chunk.chunk_id
                    ),
                    chunk_index=(
                        retrieved_chunk.chunk_index
                    ),
                    score=retrieved_chunk.score,
                    text=retrieved_chunk.text,
                    metadata=(
                        retrieved_chunk.metadata
                        or {}
                    ),
                )
            )

        return sources

    @staticmethod
    def _build_no_context_result() -> RAGResult:
        return RAGResult(
            answer=(
                "I couldn't find the answer in the "
                "uploaded documents."
            ),
            model=settings.ollama_model,
            provider="ollama",
            context_used=False,
            sources=[],
            retrieval_count=0,
            context_characters=0,
            context_truncated=False,
            usage={},
        )

    async def close(self) -> None:
        await self.retriever.close()
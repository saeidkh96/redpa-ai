from __future__ import annotations

from typing import Any
from uuid import UUID

from app.agents.state import AgentState
from app.core.exceptions import (
    LLMInvalidResponseError,
    LLMServiceError,
)
from app.services.rag_service import (
    RAGService,
    RAGServiceError,
)


def _get_latest_user_message(
    state: AgentState,
) -> str:
    messages = state.get("messages", [])

    for message in reversed(messages):
        if message.get("role") != "user":
            continue

        content = message.get("content", "")

        if not isinstance(content, str):
            continue

        cleaned_content = content.strip()

        if cleaned_content:
            return cleaned_content

    raise LLMInvalidResponseError(
        "The RAG agent received no valid user question."
    )


def _parse_uuid(
    value: object,
    *,
    field_name: str,
) -> UUID:
    if not isinstance(value, str) or not value.strip():
        raise LLMInvalidResponseError(
            f"The RAG agent received no valid {field_name}."
        )

    try:
        return UUID(value)

    except ValueError as exception:
        raise LLMInvalidResponseError(
            f"The RAG agent received an invalid {field_name}."
        ) from exception


def _serialize_sources(
    sources: list[Any],
) -> list[dict[str, Any]]:
    serialized_sources: list[dict[str, Any]] = []

    for source in sources:
        serialized_sources.append(
            {
                "source_number": source.source_number,
                "document_id": source.document_id,
                "chunk_id": source.chunk_id,
                "chunk_index": source.chunk_index,
                "score": source.score,
                "text": source.text,
                "metadata": source.metadata,
            }
        )

    return serialized_sources


async def rag_node(
    state: AgentState,
) -> dict[str, object]:
    question = _get_latest_user_message(
        state,
    )

    user_id = _parse_uuid(
        state.get("user_id"),
        field_name="user ID",
    )

    conversation_id = _parse_uuid(
        state.get("conversation_id"),
        field_name="conversation ID",
    )

    rag_service = RAGService(
        default_limit=5,
        default_score_threshold=0.20,
        default_max_context_characters=12_000,
    )

    try:
        result = await rag_service.answer(
            question=question,
            user_id=user_id,
            conversation_id=conversation_id,
        )

    except LLMServiceError:
        raise

    except RAGServiceError as exception:
        raise LLMInvalidResponseError(
            "The RAG agent could not generate a response: "
            f"{exception}"
        ) from exception

    finally:
        await rag_service.close()

    rag_usage: dict[str, Any] = {
        **result.usage,
        "rag": {
            "context_used": result.context_used,
            "retrieval_count": (
                result.retrieval_count
            ),
            "context_characters": (
                result.context_characters
            ),
            "context_truncated": (
                result.context_truncated
            ),
            "sources": _serialize_sources(
                result.sources,
            ),
        },
    }

    return {
        "response_content": result.answer,
        "model": result.model,
        "provider": result.provider,
        "usage": rag_usage,
    }
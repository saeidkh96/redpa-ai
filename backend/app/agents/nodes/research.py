from __future__ import annotations

from typing import Any

from langgraph.config import get_stream_writer

from app.agents.state import AgentState
from app.core.exceptions import LLMInvalidResponseError
from app.services.research_service import (
    ResearchService,
    ResearchServiceError,
)


def _get_latest_user_message(
    state: AgentState,
) -> str:
    messages = state.get(
        "messages",
        [],
    )

    for message in reversed(
        messages,
    ):
        if not isinstance(
            message,
            dict,
        ):
            continue

        if message.get(
            "role",
        ) != "user":
            continue

        content = str(
            message.get(
                "content",
                "",
            )
            or ""
        ).strip()

        if content:
            return content

    raise LLMInvalidResponseError(
        "The research agent received no valid user query."
    )


async def research_node(
    state: AgentState,
) -> dict[str, Any]:
    query = _get_latest_user_message(
        state,
    )

    writer = get_stream_writer()

    writer(
        {
            "type": "research_started",
            "node": "research",
            "query": query,
        }
    )

    service = ResearchService(
        search_result_limit=8,
        max_evidence_characters=18_000,
    )

    try:
        result = await service.research(
            query=query,
        )

    except ResearchServiceError as exception:
        raise LLMInvalidResponseError(
            "The research agent could not complete the request: "
            f"{exception}"
        ) from exception

    serialized_evidence = [
        item.model_dump(
            mode="json",
        )
        for item in result.evidence
    ]

    writer(
        {
            "type": "research_completed",
            "node": "research",
            "evidence_count": len(
                serialized_evidence,
            ),
        }
    )

    usage = {
        **result.usage,
        "research": {
            "query": result.query,
            "evidence_count": len(
                serialized_evidence,
            ),
            "sources": serialized_evidence,
            "execution_time_ms": (
                result.execution_time_ms
            ),
        },
    }

    return {
        "research_query": result.query,
        "research_evidence": serialized_evidence,
        "research_sources": serialized_evidence,
        "research_summary": result.answer,
        "research_provider": result.provider,
        "research_error": None,
        "research_execution_time_ms": (
            result.execution_time_ms
        ),
        "response_content": result.answer,
        "model": result.model,
        "provider": result.provider,
        "usage": usage,
    }

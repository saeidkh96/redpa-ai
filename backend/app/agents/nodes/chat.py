from __future__ import annotations

from typing import Any

from langgraph.config import get_stream_writer

from app.agents.state import AgentState
from app.core.config import settings
from app.core.exceptions import (
    LLMInvalidResponseError,
    LLMServiceError,
)
from app.schemas.ollama import OllamaChatMessage
from app.services.llm_service import llm_service


ALLOWED_LLM_ROLES = {
    "system",
    "user",
    "assistant",
    "tool",
}


async def chat_node(
    state: AgentState,
) -> dict[str, Any]:
    raw_messages = state.get(
        "messages",
        [],
    )

    if not raw_messages:
        raise LLMInvalidResponseError(
            "The chat agent received no messages."
        )

    llm_messages: list[OllamaChatMessage] = []

    for raw_message in raw_messages:
        if not isinstance(raw_message, dict):
            continue

        role = str(
            raw_message.get(
                "role",
                "",
            )
            or ""
        ).strip()

        content = str(
            raw_message.get(
                "content",
                "",
            )
            or ""
        ).strip()

        if role not in ALLOWED_LLM_ROLES:
            continue

        if not content:
            continue

        llm_messages.append(
            OllamaChatMessage(
                role=role,
                content=content,
            )
        )

    if not llm_messages:
        raise LLMInvalidResponseError(
            "The chat agent could not build a valid "
            "language model request."
        )

    writer = get_stream_writer()

    response_parts: list[str] = []

    try:
        async for token in llm_service.stream_generate(
            messages=llm_messages,
        ):
            if not token:
                continue

            response_parts.append(
                token,
            )

            writer(
                {
                    "type": "token",
                    "node": "chat",
                    "content": token,
                }
            )

    except LLMServiceError:
        raise

    except Exception as exception:
        raise LLMInvalidResponseError(
            "The chat agent failed while streaming the "
            f"language model response: {exception}"
        ) from exception

    response_content = "".join(
        response_parts
    ).strip()

    if not response_content:
        raise LLMInvalidResponseError(
            "The chat agent returned an empty response."
        )

    writer(
        {
            "type": "stream_completed",
            "node": "chat",
        }
    )

    return {
        "response_content": response_content,
        "model": settings.ollama_model,
        "provider": "ollama",
        "usage": {
            "streamed": True,
        },
    }
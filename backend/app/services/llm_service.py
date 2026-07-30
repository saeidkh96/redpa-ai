from collections.abc import AsyncIterator
from typing import Any

from app.clients.ollama_client import ollama_client
from app.schemas.ollama import (
    OllamaChatMessage,
    OllamaChatResponse,
)


class LLMService:
    async def generate(
        self,
        messages: list[OllamaChatMessage],
        *,
        response_format: str | dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> OllamaChatResponse:
        return await ollama_client.chat(
            messages=messages,
            response_format=response_format,
            temperature=temperature,
        )

    async def stream_generate(
        self,
        messages: list[OllamaChatMessage],
        *,
        response_format: str | dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        async for token in ollama_client.stream_chat(
            messages=messages,
            response_format=response_format,
            temperature=temperature,
        ):
            yield token


llm_service = LLMService()
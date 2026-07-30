from collections.abc import AsyncIterator

from app.clients.ollama_client import ollama_client
from app.schemas.ollama import (
    OllamaChatMessage,
    OllamaChatResponse,
)


class LLMService:
    async def generate(
        self,
        messages: list[OllamaChatMessage],
    ) -> OllamaChatResponse:
        return await ollama_client.chat(
            messages=messages,
        )

    async def stream_generate(
        self,
        messages: list[OllamaChatMessage],
    ) -> AsyncIterator[str]:
        async for token in ollama_client.stream_chat(
            messages=messages,
        ):
            yield token


llm_service = LLMService()
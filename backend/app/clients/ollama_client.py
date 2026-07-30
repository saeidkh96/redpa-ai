import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import (
    LLMConnectionError,
    LLMInvalidResponseError,
    LLMTimeoutError,
)
from app.schemas.ollama import (
    OllamaChatMessage,
    OllamaChatRequest,
    OllamaChatResponse,
    OllamaHealthResponse,
)


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            base_url or settings.ollama_base_url
        ).rstrip("/")

        self.model = model or settings.ollama_model

        self.timeout_seconds = (
            timeout_seconds
            or settings.ollama_timeout_seconds
        )

    def _build_chat_request(
        self,
        messages: list[OllamaChatMessage],
        *,
        stream: bool,
        response_format: str | dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> OllamaChatRequest:
        selected_temperature = (
            settings.ollama_temperature
            if temperature is None
            else temperature
        )

        return OllamaChatRequest(
            model=self.model,
            messages=messages,
            stream=stream,
            format=response_format,
            options={
                "temperature": selected_temperature,
            },
        )

    def _create_timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            timeout=self.timeout_seconds,
            connect=10.0,
        )

    async def chat(
        self,
        messages: list[OllamaChatMessage],
        *,
        response_format: str | dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> OllamaChatResponse:
        request_data = self._build_chat_request(
            messages,
            stream=False,
            response_format=response_format,
            temperature=temperature,
        )

        try:
            async with httpx.AsyncClient(
                timeout=self._create_timeout(),
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=request_data.model_dump(
                        exclude_none=True,
                    ),
                )
                response.raise_for_status()

        except httpx.ConnectError as exception:
            raise LLMConnectionError(
                "Could not connect to Ollama. "
                "Make sure Ollama is installed and running."
            ) from exception

        except httpx.TimeoutException as exception:
            raise LLMTimeoutError(
                "Ollama did not respond before the request timed out."
            ) from exception

        except httpx.HTTPStatusError as exception:
            raise LLMInvalidResponseError(
                "Ollama returned an unsuccessful response. "
                f"Status: {exception.response.status_code}. "
                f"Response: {exception.response.text}"
            ) from exception

        except httpx.RequestError as exception:
            raise LLMConnectionError(
                f"Could not communicate with Ollama: {exception}"
            ) from exception

        try:
            parsed_response = OllamaChatResponse.model_validate(
                response.json(),
            )
        except (ValueError, ValidationError) as exception:
            raise LLMInvalidResponseError(
                "Ollama returned an invalid JSON response."
            ) from exception

        if not parsed_response.message.content.strip():
            raise LLMInvalidResponseError(
                "Ollama returned an empty assistant response."
            )

        return parsed_response

    async def stream_chat(
        self,
        messages: list[OllamaChatMessage],
        *,
        response_format: str | dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        request_data = self._build_chat_request(
            messages,
            stream=True,
            response_format=response_format,
            temperature=temperature,
        )

        received_content = False
        stream_completed = False

        try:
            async with httpx.AsyncClient(
                timeout=self._create_timeout(),
            ) as client:
                async with client.stream(
                    method="POST",
                    url=f"{self.base_url}/api/chat",
                    json=request_data.model_dump(
                        exclude_none=True,
                    ),
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        try:
                            payload = json.loads(line)
                        except json.JSONDecodeError as exception:
                            raise LLMInvalidResponseError(
                                "Ollama returned an invalid streaming "
                                "JSON response."
                            ) from exception

                        error_message = payload.get("error")
                        if error_message:
                            raise LLMInvalidResponseError(
                                "Ollama returned a streaming error: "
                                f"{error_message}"
                            )

                        message = payload.get("message") or {}
                        content = message.get("content")

                        if content is not None:
                            if not isinstance(content, str):
                                raise LLMInvalidResponseError(
                                    "Ollama returned invalid streaming "
                                    "message content."
                                )

                            if content:
                                received_content = True
                                yield content

                        if payload.get("done") is True:
                            stream_completed = True
                            break

        except LLMInvalidResponseError:
            raise

        except httpx.ConnectError as exception:
            raise LLMConnectionError(
                "Could not connect to Ollama. "
                "Make sure Ollama is installed and running."
            ) from exception

        except httpx.TimeoutException as exception:
            raise LLMTimeoutError(
                "Ollama streaming response timed out."
            ) from exception

        except httpx.HTTPStatusError as exception:
            try:
                response_bytes = await exception.response.aread()
                response_text = response_bytes.decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                response_text = (
                    "Could not read the Ollama error response."
                )

            raise LLMInvalidResponseError(
                "Ollama returned an unsuccessful streaming response. "
                f"Status: {exception.response.status_code}. "
                f"Response: {response_text}"
            ) from exception

        except httpx.RequestError as exception:
            raise LLMConnectionError(
                "Could not communicate with Ollama while streaming: "
                f"{exception}"
            ) from exception

        if not stream_completed:
            raise LLMInvalidResponseError(
                "Ollama closed the stream before completing the response."
            )

        if not received_content:
            raise LLMInvalidResponseError(
                "Ollama returned an empty streaming response."
            )

    async def health_check(
        self,
    ) -> OllamaHealthResponse:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0),
            ) as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                )
                response.raise_for_status()

            response_data = response.json()

            installed_models = [
                model.get("name", "")
                for model in response_data.get("models", [])
                if model.get("name")
            ]

            return OllamaHealthResponse(
                available=True,
                base_url=self.base_url,
                configured_model=self.model,
                installed_models=installed_models,
            )

        except (httpx.HTTPError, ValueError) as exception:
            return OllamaHealthResponse(
                available=False,
                base_url=self.base_url,
                configured_model=self.model,
                installed_models=[],
                error=str(exception),
            )


ollama_client = OllamaClient()
from __future__ import annotations

import json
import logging
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


logger = logging.getLogger(__name__)


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

    def _create_timeout(
        self,
        *,
        streaming: bool,
    ) -> httpx.Timeout:
        """
        Build an HTTP timeout suitable for local LLM generation.

        Streaming generation can legitimately take several minutes.
        A finite read timeout can close the response before Ollama sends
        its final ``done=true`` frame, so streaming reads are unlimited.
        Connection, write, and pool waits remain bounded.
        """

        if streaming:
            return httpx.Timeout(
                connect=10.0,
                read=None,
                write=30.0,
                pool=10.0,
            )

        return httpx.Timeout(
            timeout=self.timeout_seconds,
            connect=10.0,
        )

    @staticmethod
    def _create_limits() -> httpx.Limits:
        return httpx.Limits(
            max_connections=20,
            max_keepalive_connections=10,
            keepalive_expiry=30.0,
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
                timeout=self._create_timeout(
                    streaming=False,
                ),
                limits=self._create_limits(),
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
        final_done_reason: str | None = None

        try:
            async with httpx.AsyncClient(
                timeout=self._create_timeout(
                    streaming=True,
                ),
                limits=self._create_limits(),
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
                        normalized_line = line.strip()

                        if not normalized_line:
                            continue

                        try:
                            payload = json.loads(
                                normalized_line,
                            )

                        except json.JSONDecodeError as exception:
                            raise LLMInvalidResponseError(
                                "Ollama returned an invalid streaming "
                                "JSON response."
                            ) from exception

                        if not isinstance(payload, dict):
                            raise LLMInvalidResponseError(
                                "Ollama returned an invalid streaming "
                                "payload."
                            )

                        error_message = payload.get(
                            "error",
                        )

                        if error_message:
                            raise LLMInvalidResponseError(
                                "Ollama returned a streaming error: "
                                f"{error_message}"
                            )

                        message = payload.get(
                            "message",
                        )

                        if message is None:
                            message = {}

                        if not isinstance(message, dict):
                            raise LLMInvalidResponseError(
                                "Ollama returned an invalid streaming "
                                "message object."
                            )

                        content = message.get(
                            "content",
                        )

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

                            done_reason = payload.get(
                                "done_reason",
                            )

                            if isinstance(done_reason, str):
                                final_done_reason = done_reason

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

        if not received_content:
            raise LLMInvalidResponseError(
                "Ollama returned an empty streaming response."
            )

        if not stream_completed:
            logger.warning(
                "Ollama stream ended without a final done frame, "
                "but assistant content was received; accepting the "
                "received content | model=%s",
                self.model,
            )
            return

        logger.debug(
            "Ollama stream completed | model=%s done_reason=%s",
            self.model,
            final_done_reason,
        )

    async def health_check(
        self,
    ) -> OllamaHealthResponse:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0),
                limits=self._create_limits(),
            ) as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                )
                response.raise_for_status()

            response_data = response.json()

            installed_models = [
                model.get("name", "")
                for model in response_data.get(
                    "models",
                    [],
                )
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
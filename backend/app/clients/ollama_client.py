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

    async def chat(
        self,
        messages: list[OllamaChatMessage],
    ) -> OllamaChatResponse:
        request_data = OllamaChatRequest(
            model=self.model,
            messages=messages,
            stream=False,
            options={
                "temperature": settings.ollama_temperature,
            },
        )

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    self.timeout_seconds,
                ),
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
            response_text = exception.response.text

            raise LLMInvalidResponseError(
                "Ollama returned an unsuccessful response. "
                f"Status: {exception.response.status_code}. "
                f"Response: {response_text}"
            ) from exception

        except httpx.RequestError as exception:
            raise LLMConnectionError(
                f"Could not communicate with Ollama: {exception}"
            ) from exception

        try:
            parsed_response = OllamaChatResponse.model_validate(
                response.json(),
            )
        except (
            ValueError,
            ValidationError,
        ) as exception:
            raise LLMInvalidResponseError(
                "Ollama returned an invalid JSON response."
            ) from exception

        assistant_content = (
            parsed_response.message.content.strip()
        )

        if not assistant_content:
            raise LLMInvalidResponseError(
                "Ollama returned an empty assistant response."
            )

        return parsed_response

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

        except (
            httpx.HTTPError,
            ValueError,
        ) as exception:
            return OllamaHealthResponse(
                available=False,
                base_url=self.base_url,
                configured_model=self.model,
                installed_models=[],
                error=str(exception),
            )


ollama_client = OllamaClient()
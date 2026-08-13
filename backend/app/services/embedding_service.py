from __future__ import annotations

from typing import Any

import httpx


class EmbeddingServiceError(Exception):
    """Raised when generating embeddings fails."""


class EmbeddingService:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text:latest",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate an embedding vector for a single text.
        """
        cleaned_text = text.strip()

        if not cleaned_text:
            raise ValueError("Text cannot be empty.")

        embeddings = await self.embed_texts([cleaned_text])

        if not embeddings:
            raise EmbeddingServiceError(
                "Ollama returned no embedding vector."
            )

        return embeddings[0]

    async def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embedding vectors for multiple texts in one request.
        """
        cleaned_texts = [
            text.strip()
            for text in texts
            if text and text.strip()
        ]

        if not cleaned_texts:
            raise ValueError(
                "At least one non-empty text is required."
            )

        payload = {
            "model": self.model,
            "input": cleaned_texts,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.ConnectError as exc:
            raise EmbeddingServiceError(
                f"Could not connect to Ollama at "
                f"{self.base_url}."
            ) from exc

        except httpx.TimeoutException as exc:
            raise EmbeddingServiceError(
                "Ollama embedding request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            error_message = self._extract_error_message(
                exc.response
            )

            raise EmbeddingServiceError(
                f"Ollama embedding request failed: "
                f"{error_message}"
            ) from exc

        except httpx.HTTPError as exc:
            raise EmbeddingServiceError(
                f"Ollama request failed: {exc}"
            ) from exc

        data: dict[str, Any] = response.json()
        embeddings = data.get("embeddings")

        if not isinstance(embeddings, list):
            raise EmbeddingServiceError(
                "Invalid response from Ollama: "
                "'embeddings' field is missing."
            )

        if len(embeddings) != len(cleaned_texts):
            raise EmbeddingServiceError(
                "Ollama returned an unexpected number "
                "of embedding vectors."
            )

        validated_embeddings: list[list[float]] = []

        for embedding in embeddings:
            if not isinstance(embedding, list):
                raise EmbeddingServiceError(
                    "Invalid embedding vector returned "
                    "by Ollama."
                )

            validated_embeddings.append(
                [float(value) for value in embedding]
            )

        return validated_embeddings

    async def health_check(self) -> dict[str, Any]:
        """
        Check whether Ollama is reachable and the model exists.
        """
        try:
            async with httpx.AsyncClient(
                timeout=10.0
            ) as client:
                response = await client.get(
                    f"{self.base_url}/api/tags"
                )

                response.raise_for_status()

        except httpx.HTTPError as exc:
            return {
                "available": False,
                "model": self.model,
                "base_url": self.base_url,
                "error": str(exc),
            }

        data = response.json()
        models = data.get("models", [])

        available_models = {
            model.get("name")
            for model in models
            if isinstance(model, dict)
        }

        return {
            "available": self.model in available_models,
            "model": self.model,
            "base_url": self.base_url,
            "installed_models": sorted(
                model
                for model in available_models
                if model
            ),
        }

    @staticmethod
    def _extract_error_message(
        response: httpx.Response,
    ) -> str:
        try:
            data = response.json()
        except ValueError:
            return response.text or str(
                response.status_code
            )

        return str(
            data.get("error")
            or data.get("detail")
            or response.status_code
        )
"""Langfuse tracing for RedPA's provider-agnostic model gateway.

This module deliberately keeps Langfuse optional. A missing SDK, credentials,
or a temporary Langfuse outage must never stop a recruiter workflow.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Iterator, Protocol


logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class LangfuseSettings:
    enabled: bool
    capture_inputs: bool
    capture_outputs: bool
    environment: str

    @classmethod
    def from_environment(cls) -> "LangfuseSettings":
        return cls(
            enabled=_env_bool("LANGFUSE_ENABLED", False),
            capture_inputs=_env_bool("LANGFUSE_CAPTURE_INPUTS", True),
            capture_outputs=_env_bool("LANGFUSE_CAPTURE_OUTPUTS", True),
            environment=os.getenv("LANGFUSE_TRACING_ENVIRONMENT", os.getenv("ENVIRONMENT", "development")),
        )


class GenerationTrace(Protocol):
    def success(self, *, response: Any, usage: Any | None) -> None: ...
    def failure(self, error: Exception) -> None: ...


class NullGenerationTrace:
    def success(self, *, response: Any, usage: Any | None) -> None:
        pass

    def failure(self, error: Exception) -> None:
        pass


class LangfuseGenerationTrace:
    def __init__(self, observation: Any, *, started_at: float, capture_outputs: bool) -> None:
        self._observation = observation
        self._started_at = started_at
        self._capture_outputs = capture_outputs

    def success(self, *, response: Any, usage: Any | None) -> None:
        usage_details = None
        if usage is not None:
            usage_details = {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            }
        try:
            self._observation.update(
                output=response.content if self._capture_outputs else {"captured": False},
                usage_details=usage_details,
                metadata={
                    "provider": response.provider,
                    "finish_reason": response.finish_reason,
                    "latency_ms": round((perf_counter() - self._started_at) * 1000, 2),
                },
            )
        except Exception:
            logger.warning("Langfuse generation update failed.", exc_info=True)

    def failure(self, error: Exception) -> None:
        try:
            self._observation.update(
                level="ERROR",
                status_message=str(error),
                metadata={"latency_ms": round((perf_counter() - self._started_at) * 1000, 2)},
            )
        except Exception:
            logger.warning("Langfuse generation error update failed.", exc_info=True)


class LangfuseTracer:
    """Creates one generation observation for every routed provider attempt."""

    def __init__(self, settings: LangfuseSettings | None = None) -> None:
        self.settings = settings or LangfuseSettings.from_environment()
        self._client: Any | None = None
        self._unavailable = False

    def _get_client(self) -> Any | None:
        if self._client is not None:
            return self._client
        if not self.settings.enabled or self._unavailable:
            return None
        try:
            # get_client reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
            # and LANGFUSE_TRACING_ENVIRONMENT from the process environment.
            from langfuse import get_client

            self._client = self._client or get_client()
            return self._client
        except Exception:  # Observability must remain non-blocking.
            self._unavailable = True
            logger.warning("Langfuse is enabled but could not be initialized; tracing is disabled.", exc_info=True)
            return None

    @contextmanager
    def generation(
        self,
        *,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        metadata: dict[str, Any],
    ) -> Iterator[GenerationTrace]:
        client = self._get_client()
        if client is None:
            yield NullGenerationTrace()
            return

        safe_metadata = {"provider": provider, **metadata}
        trace_input: Any = {"messages": messages} if self.settings.capture_inputs else {"captured": False}
        try:
            observation = client.start_observation(
                as_type="generation",
                name="model-gateway.invoke",
                model=model,
                input=trace_input,
                metadata=safe_metadata,
            )
        except Exception:
            logger.warning("Langfuse failed to start a model observation.", exc_info=True)
            yield NullGenerationTrace()
            return

        try:
            yield LangfuseGenerationTrace(
                observation,
                started_at=perf_counter(),
                capture_outputs=self.settings.capture_outputs,
            )
        finally:
            try:
                observation.end()
            except Exception:
                logger.warning("Langfuse failed to end a model observation.", exc_info=True)

    def flush(self) -> None:
        client = self._get_client()
        if client is not None:
            try:
                client.flush()
            except Exception:
                logger.warning("Langfuse flush failed.", exc_info=True)


_tracer: LangfuseTracer | None = None


def get_langfuse_tracer() -> LangfuseTracer:
    """Return the process-wide tracer so its buffered events flush on shutdown."""
    global _tracer
    if _tracer is None:
        _tracer = LangfuseTracer()
    return _tracer

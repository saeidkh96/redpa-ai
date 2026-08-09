from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class LLMCapability(str, enum.Enum):
    CHAT = "chat"
    JSON_OUTPUT = "json_output"
    STREAMING = "streaming"
    TOOLS = "tools"
    VISION = "vision"


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: str
    content: str

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise ValueError("Message role cannot be empty.")
        if not self.content.strip():
            raise ValueError("Message content cannot be empty.")


@dataclass(frozen=True, slots=True)
class LLMUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class LLMRequest:
    messages: tuple[LLMMessage, ...]
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    response_format: str | dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.messages:
            raise ValueError("At least one message is required.")
        if self.temperature is not None and not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0.")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero.")


@dataclass(frozen=True, slots=True)
class LLMResponse:
    provider: str
    model: str
    content: str
    finish_reason: str | None = None
    usage: LLMUsage | None = None
    raw: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class LLMProviderHealth:
    provider: str
    available: bool
    models: tuple[str, ...] = ()
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    name: str
    provider_type: str
    default_model: str
    capabilities: frozenset[LLMCapability]
    enabled: bool = True


class LLMProviderError(RuntimeError):
    def __init__(self, message: str, *, provider: str, retryable: bool = False, status_code: int | None = None) -> None:
        super().__init__(message)
        self.provider = provider
        self.retryable = retryable
        self.status_code = status_code


class LLMProvider(ABC):
    @property
    @abstractmethod
    def descriptor(self) -> ProviderDescriptor:
        raise NotImplementedError

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> LLMProviderHealth:
        raise NotImplementedError

    def supports(self, capability: LLMCapability) -> bool:
        return capability in self.descriptor.capabilities

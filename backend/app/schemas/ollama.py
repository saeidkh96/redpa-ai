from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class OllamaChatMessage(BaseModel):
    role: Literal[
        "system",
        "user",
        "assistant",
        "tool",
    ]
    content: str


class OllamaChatRequest(BaseModel):
    model: str
    messages: list[OllamaChatMessage]
    stream: bool = False

    # Supports Ollama JSON mode:
    # - "json"
    # - a full JSON schema dictionary
    format: str | dict[str, Any] | None = None

    options: dict[str, Any] | None = None


class OllamaResponseMessage(BaseModel):
    role: str
    content: str


class OllamaChatResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )

    model: str
    message: OllamaResponseMessage
    done: bool = False

    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None


class OllamaHealthResponse(BaseModel):
    available: bool
    base_url: str
    configured_model: str
    installed_models: list[str] = Field(
        default_factory=list,
    )
    error: str | None = None
from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    name: str
    provider_type: str
    base_url: str
    default_model: str
    api_key: str | None = None
    timeout_seconds: float = 120.0
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ModelGatewayConfig:
    default_provider: str
    providers: tuple[ProviderConfig, ...]

    @classmethod
    def from_environment(cls) -> "ModelGatewayConfig":
        ollama = ProviderConfig(
            name="ollama",
            provider_type="ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
            default_model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            timeout_seconds=_env_float("OLLAMA_TIMEOUT_SECONDS", 120.0),
            enabled=_env_bool("MODEL_GATEWAY_OLLAMA_ENABLED", True),
        )
        openai = ProviderConfig(
            name="openai",
            provider_type="openai_compatible",
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/"),
            default_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout_seconds=_env_float("OPENAI_TIMEOUT_SECONDS", 120.0),
            enabled=_env_bool("MODEL_GATEWAY_OPENAI_ENABLED", False),
        )
        anthropic = ProviderConfig(
            name="anthropic",
            provider_type="anthropic",
            base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/"),
            default_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            timeout_seconds=_env_float("ANTHROPIC_TIMEOUT_SECONDS", 120.0),
            enabled=_env_bool("MODEL_GATEWAY_ANTHROPIC_ENABLED", False),
        )
        gemini = ProviderConfig(
            name="gemini",
            provider_type="gemini",
            base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com").rstrip("/"),
            default_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            api_key=os.getenv("GEMINI_API_KEY"),
            timeout_seconds=_env_float("GEMINI_TIMEOUT_SECONDS", 120.0),
            enabled=_env_bool("MODEL_GATEWAY_GEMINI_ENABLED", False),
        )
        compatible = ProviderConfig(
            name=os.getenv("OPENAI_COMPATIBLE_PROVIDER_NAME", "openai-compatible"),
            provider_type="openai_compatible",
            base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com").rstrip("/"),
            default_model=os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-4.1-mini"),
            api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY"),
            timeout_seconds=_env_float("OPENAI_COMPATIBLE_TIMEOUT_SECONDS", 120.0),
            enabled=_env_bool("MODEL_GATEWAY_OPENAI_COMPATIBLE_ENABLED", False),
        )
        return cls(
            default_provider=os.getenv("MODEL_GATEWAY_DEFAULT_PROVIDER", "ollama"),
            providers=(ollama, openai, anthropic, gemini, compatible),
        )

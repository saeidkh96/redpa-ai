from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

from app.model_gateway.contracts import (
    LLMCapability,
    LLMProvider,
)
from app.model_gateway.economics import ModelEconomicsCatalog
from app.model_gateway.registry import (
    LLMProviderRegistry,
    ProviderNotFoundError,
)


@dataclass(frozen=True, slots=True)
class ModelRoute:
    provider: str
    model: str | None = None
    reason: str = "default"
    fallback_providers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RoutingContext:
    agent_id: str | None = None
    requested_provider: str | None = None
    requested_model: str | None = None
    required_capability: LLMCapability = LLMCapability.CHAT
    metadata: dict[str, Any] | None = None


class RoutingStrategy(Protocol):
    def select(
        self,
        *,
        registry: LLMProviderRegistry,
        context: RoutingContext,
    ) -> ModelRoute | None:
        ...


class ExplicitRoutingStrategy:
    """Highest-priority route when the caller explicitly selects a provider."""

    def select(
        self,
        *,
        registry: LLMProviderRegistry,
        context: RoutingContext,
    ) -> ModelRoute | None:
        if not context.requested_provider:
            return None

        provider = registry.get(context.requested_provider)

        if not provider.supports(context.required_capability):
            raise ProviderNotFoundError(
                f"Provider {context.requested_provider!r} does not support "
                f"{context.required_capability.value!r}.",
            )

        return ModelRoute(
            provider=provider.descriptor.name,
            model=context.requested_model or provider.descriptor.default_model,
            reason="explicit",
        )


class AgentRoutingStrategy:
    """Per-agent provider/model selection."""

    def __init__(
        self,
        routes: dict[str, ModelRoute],
    ) -> None:
        self._routes = routes

    @classmethod
    def from_environment(cls) -> "AgentRoutingStrategy":
        raw = os.getenv("MODEL_GATEWAY_AGENT_ROUTES_JSON", "").strip()
        routes: dict[str, ModelRoute] = {}

        if raw:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "MODEL_GATEWAY_AGENT_ROUTES_JSON is not valid JSON.",
                ) from exc

            if not isinstance(payload, dict):
                raise ValueError(
                    "MODEL_GATEWAY_AGENT_ROUTES_JSON must be a JSON object.",
                )

            for agent_id, item in payload.items():
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Agent route {agent_id!r} must be an object.",
                    )

                provider = str(item.get("provider", "")).strip()
                if not provider:
                    raise ValueError(
                        f"Agent route {agent_id!r} requires provider.",
                    )

                fallback = item.get("fallback_providers", [])
                if not isinstance(fallback, list):
                    raise ValueError(
                        f"fallback_providers for {agent_id!r} must be a list.",
                    )

                routes[str(agent_id)] = ModelRoute(
                    provider=provider,
                    model=(
                        str(item["model"])
                        if item.get("model")
                        else None
                    ),
                    reason="agent",
                    fallback_providers=tuple(
                        str(value)
                        for value in fallback
                        if str(value).strip()
                    ),
                )

        return cls(routes)

    def select(
        self,
        *,
        registry: LLMProviderRegistry,
        context: RoutingContext,
    ) -> ModelRoute | None:
        if not context.agent_id:
            return None

        route = self._routes.get(context.agent_id)
        if route is None:
            return None

        provider = registry.get(route.provider)

        if not provider.supports(context.required_capability):
            raise ProviderNotFoundError(
                f"Agent route provider {route.provider!r} does not support "
                f"{context.required_capability.value!r}.",
            )

        return ModelRoute(
            provider=provider.descriptor.name,
            model=context.requested_model
            or route.model
            or provider.descriptor.default_model,
            reason=route.reason,
            fallback_providers=route.fallback_providers,
        )


class CostAwareRoutingStrategy:
    """Routes to the cheapest capability-compatible provider when requested."""

    def __init__(self, catalog: ModelEconomicsCatalog | None = None) -> None:
        self.catalog = catalog or ModelEconomicsCatalog.from_environment()

    def select(self, *, registry: LLMProviderRegistry, context: RoutingContext) -> ModelRoute | None:
        metadata = context.metadata or {}
        if str(metadata.get("routing_mode", "")).lower() not in {"cost", "cost_aware", "cheapest"}:
            return None
        candidates = registry.providers_supporting(context.required_capability)
        allowed = metadata.get("allowed_providers")
        if isinstance(allowed, (list, tuple, set, frozenset)) and allowed:
            allowed_names = {str(name) for name in allowed}
            candidates = [p for p in candidates if p.descriptor.name in allowed_names]
        if not candidates:
            return None
        estimated_input = int(metadata.get("estimated_input_tokens", 1000) or 1000)
        estimated_output = int(metadata.get("estimated_output_tokens", 500) or 500)
        ranked = sorted(
            candidates,
            key=lambda p: self.catalog.get(p.descriptor.name, context.requested_model or p.descriptor.default_model).estimate(estimated_input, estimated_output),
        )
        selected = ranked[0]
        fallbacks = tuple(p.descriptor.name for p in ranked[1:])
        return ModelRoute(
            provider=selected.descriptor.name,
            model=context.requested_model or selected.descriptor.default_model,
            reason="cost_aware",
            fallback_providers=fallbacks,
        )


class CapabilityRoutingStrategy:
    """Selects the first enabled provider supporting the required capability."""

    def select(
        self,
        *,
        registry: LLMProviderRegistry,
        context: RoutingContext,
    ) -> ModelRoute | None:
        providers = registry.providers_supporting(
            context.required_capability,
        )

        if not providers:
            return None

        default = registry.get()
        if default in providers:
            provider = default
            reason = "default_capability"
        else:
            provider = providers[0]
            reason = "capability"

        return ModelRoute(
            provider=provider.descriptor.name,
            model=context.requested_model or provider.descriptor.default_model,
            reason=reason,
        )


class CompositeRoutingStrategy:
    """Strategy Pattern: evaluate routing policies in priority order."""

    def __init__(
        self,
        strategies: tuple[RoutingStrategy, ...],
        *,
        global_fallback_providers: tuple[str, ...] = (),
    ) -> None:
        self._strategies = strategies
        self._global_fallback_providers = global_fallback_providers

    @classmethod
    def from_environment(cls) -> "CompositeRoutingStrategy":
        fallback_raw = os.getenv(
            "MODEL_GATEWAY_FALLBACK_PROVIDERS",
            "",
        )

        fallback = tuple(
            item.strip()
            for item in fallback_raw.split(",")
            if item.strip()
        )

        return cls(
            (
                ExplicitRoutingStrategy(),
                AgentRoutingStrategy.from_environment(),
                CostAwareRoutingStrategy(),
                CapabilityRoutingStrategy(),
            ),
            global_fallback_providers=fallback,
        )

    def select(
        self,
        *,
        registry: LLMProviderRegistry,
        context: RoutingContext,
    ) -> ModelRoute:
        for strategy in self._strategies:
            route = strategy.select(
                registry=registry,
                context=context,
            )
            if route is None:
                continue

            fallback = tuple(
                name
                for name in (
                    *route.fallback_providers,
                    *self._global_fallback_providers,
                )
                if name != route.provider and name in registry
            )

            return ModelRoute(
                provider=route.provider,
                model=route.model,
                reason=route.reason,
                fallback_providers=tuple(dict.fromkeys(fallback)),
            )

        raise ProviderNotFoundError(
            "No enabled provider satisfies the routing request.",
        )

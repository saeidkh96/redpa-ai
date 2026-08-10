from __future__ import annotations

from dataclasses import dataclass

from app.model_gateway.contracts import (
    LLMCapability,
    LLMProviderError,
    LLMProviderHealth,
    LLMRequest,
    LLMResponse,
)
from app.model_gateway.registry import (
    LLMProviderRegistry,
    ProviderNotFoundError,
)
from app.model_gateway.reliability import (
    ReliableProviderExecutor,
)
from app.model_gateway.routing import (
    CompositeRoutingStrategy,
    ModelRoute,
    RoutingContext,
)


@dataclass(frozen=True, slots=True)
class GatewayResult:
    response: LLMResponse
    route: ModelRoute
    attempted_providers: tuple[str, ...]


class ModelGateway:
    def __init__(
        self,
        *,
        registry: LLMProviderRegistry,
        router: CompositeRoutingStrategy | None = None,
        executor: ReliableProviderExecutor | None = None,
    ) -> None:
        self.registry = registry
        self.router = router or CompositeRoutingStrategy.from_environment()
        self.executor = executor or ReliableProviderExecutor()

    def preview_route(
        self,
        *,
        agent_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        capability: LLMCapability = LLMCapability.CHAT,
    ) -> ModelRoute:
        return self.router.select(
            registry=self.registry,
            context=RoutingContext(
                agent_id=agent_id,
                requested_provider=provider,
                requested_model=model,
                required_capability=capability,
            ),
        )

    async def invoke(
        self,
        *,
        request: LLMRequest,
        agent_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        capability: LLMCapability = LLMCapability.CHAT,
        allowed_providers: frozenset[str] | set[str] | None = None,
    ) -> GatewayResult:
        route = self.preview_route(
            agent_id=agent_id,
            provider=provider,
            model=model or request.model,
            capability=capability,
        )

        candidates = (
            route.provider,
            *route.fallback_providers,
        )

        if allowed_providers is not None:
            candidates = tuple(
                name for name in candidates
                if name in allowed_providers
            )
            if not candidates:
                raise ProviderNotFoundError(
                    "No routed model provider is allowed by tenant governance.",
                )

        attempted: list[str] = []
        last_error: Exception | None = None

        for provider_name in candidates:
            attempted.append(provider_name)

            try:
                selected = self.registry.get(provider_name)
            except ProviderNotFoundError as exc:
                last_error = exc
                continue

            target_model = (
                route.model
                if provider_name == route.provider
                else selected.descriptor.default_model
            )

            provider_request = LLMRequest(
                messages=request.messages,
                model=target_model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=request.response_format,
                metadata=request.metadata,
            )

            try:
                response = await self.executor.execute(
                    provider=selected,
                    request=provider_request,
                )

                return GatewayResult(
                    response=response,
                    route=route,
                    attempted_providers=tuple(attempted),
                )

            except LLMProviderError as exc:
                last_error = exc

                if not exc.retryable:
                    break

        if isinstance(last_error, Exception):
            raise last_error

        raise ProviderNotFoundError(
            "No model provider could execute the request.",
        )

    async def health(self) -> list[LLMProviderHealth]:
        return await self.registry.health()

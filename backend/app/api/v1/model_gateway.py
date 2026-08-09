from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser
from app.model_gateway.bootstrap import model_gateway
from app.model_gateway.contracts import (
    LLMMessage,
    LLMProviderError,
    LLMRequest,
)
from app.model_gateway.registry import ProviderNotFoundError
from app.schemas.model_gateway import (
    CircuitBreakerResponse,
    GatewayInvokeRequest,
    GatewayInvokeResponse,
    GatewayRoutePreviewRequest,
    GatewayRouteResponse,
    GatewayUsageResponse,
    ProviderDescriptorResponse,
    ProviderHealthResponse,
)


router = APIRouter(
    prefix="/model-gateway",
    tags=["Model Gateway"],
)


@router.get(
    "/providers",
    response_model=list[ProviderDescriptorResponse],
)
async def list_providers(
    current_user: CurrentUser,
) -> list[ProviderDescriptorResponse]:
    del current_user

    return [
        ProviderDescriptorResponse(
            name=item.name,
            provider_type=item.provider_type,
            default_model=item.default_model,
            capabilities=sorted(
                capability.value
                for capability in item.capabilities
            ),
            enabled=item.enabled,
        )
        for item in model_gateway.registry.descriptors()
    ]


@router.get(
    "/health",
    response_model=list[ProviderHealthResponse],
)
async def provider_health(
    current_user: CurrentUser,
) -> list[ProviderHealthResponse]:
    del current_user

    health = await model_gateway.health()

    return [
        ProviderHealthResponse(
            provider=item.provider,
            available=item.available,
            models=list(item.models),
            detail=item.detail,
        )
        for item in health
    ]


@router.get(
    "/circuits",
    response_model=list[CircuitBreakerResponse],
)
async def circuit_breakers(
    current_user: CurrentUser,
) -> list[CircuitBreakerResponse]:
    del current_user

    snapshot = model_gateway.executor.circuit_snapshot()

    return [
        CircuitBreakerResponse(
            provider=provider,
            state=str(item["state"]),
            failures=int(item["failures"]),
            failure_threshold=int(item["failure_threshold"]),
            recovery_timeout_seconds=float(
                item["recovery_timeout_seconds"],
            ),
        )
        for provider, item in sorted(snapshot.items())
    ]


@router.post(
    "/route",
    response_model=GatewayRouteResponse,
)
async def preview_route(
    request: GatewayRoutePreviewRequest,
    current_user: CurrentUser,
) -> GatewayRouteResponse:
    del current_user

    try:
        route = model_gateway.preview_route(
            agent_id=request.agent_id,
            provider=request.provider,
            model=request.model,
            capability=request.capability,
        )
    except ProviderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return GatewayRouteResponse(
        provider=route.provider,
        model=route.model,
        reason=route.reason,
        fallback_providers=list(route.fallback_providers),
    )


@router.post(
    "/invoke",
    response_model=GatewayInvokeResponse,
)
async def invoke_model(
    request: GatewayInvokeRequest,
    current_user: CurrentUser,
) -> GatewayInvokeResponse:
    del current_user

    llm_request = LLMRequest(
        messages=tuple(
            LLMMessage(
                role=message.role,
                content=message.content,
            )
            for message in request.messages
        ),
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        response_format=request.response_format,
        metadata=request.metadata,
    )

    try:
        result = await model_gateway.invoke(
            request=llm_request,
            agent_id=request.agent_id,
            provider=request.provider,
            model=request.model,
            capability=request.capability,
        )
    except ProviderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "provider": exc.provider,
                "message": str(exc),
                "retryable": exc.retryable,
                "status_code": exc.status_code,
            },
        ) from exc

    usage = result.response.usage

    return GatewayInvokeResponse(
        provider=result.response.provider,
        model=result.response.model,
        content=result.response.content,
        finish_reason=result.response.finish_reason,
        usage=(
            GatewayUsageResponse(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
            )
            if usage is not None
            else None
        ),
        route=GatewayRouteResponse(
            provider=result.route.provider,
            model=result.route.model,
            reason=result.route.reason,
            fallback_providers=list(
                result.route.fallback_providers,
            ),
        ),
        attempted_providers=list(result.attempted_providers),
    )

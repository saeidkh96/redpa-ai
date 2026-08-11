from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.model_gateway.bootstrap import model_gateway
from app.model_gateway.contracts import LLMMessage, LLMProviderError, LLMRequest
from app.model_gateway.registry import ProviderNotFoundError
from app.security.rbac import Permission, authorize
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
from app.services.platform_v4_model_governance_service import (
    ModelPricingCatalog,
    PlatformModelGovernanceService,
)
from app.services.tenant_service import TenantMembershipNotFoundError, TenantService


router = APIRouter(prefix="/model-gateway", tags=["Model Gateway"])
pricing_catalog = ModelPricingCatalog.from_environment()


@router.get("/providers", response_model=list[ProviderDescriptorResponse])
async def list_providers(current_user: CurrentUser) -> list[ProviderDescriptorResponse]:
    del current_user
    return [
        ProviderDescriptorResponse(
            name=item.name,
            provider_type=item.provider_type,
            default_model=item.default_model,
            capabilities=sorted(capability.value for capability in item.capabilities),
            enabled=item.enabled,
        )
        for item in model_gateway.registry.descriptors()
    ]


@router.get("/health", response_model=list[ProviderHealthResponse])
async def provider_health(current_user: CurrentUser) -> list[ProviderHealthResponse]:
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


@router.get("/circuits", response_model=list[CircuitBreakerResponse])
async def circuit_breakers(current_user: CurrentUser) -> list[CircuitBreakerResponse]:
    del current_user
    snapshot = model_gateway.executor.circuit_snapshot()
    return [
        CircuitBreakerResponse(
            provider=provider,
            state=str(item["state"]),
            failures=int(item["failures"]),
            failure_threshold=int(item["failure_threshold"]),
            recovery_timeout_seconds=float(item["recovery_timeout_seconds"]),
        )
        for provider, item in sorted(snapshot.items())
    ]


@router.post("/route", response_model=GatewayRouteResponse)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return GatewayRouteResponse(
        provider=route.provider,
        model=route.model,
        reason=route.reason,
        fallback_providers=list(route.fallback_providers),
    )


@router.post("/invoke", response_model=GatewayInvokeResponse)
async def invoke_model(
    request: GatewayInvokeRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> GatewayInvokeResponse:
    llm_request = LLMRequest(
        messages=tuple(LLMMessage(role=message.role, content=message.content) for message in request.messages),
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        response_format=request.response_format,
        metadata=request.metadata,
    )

    allowed_providers: frozenset[str] | None = None
    governance_route = None

    if request.tenant_id is not None:
        try:
            membership = await TenantService.get_membership(
                session=session,
                tenant_id=request.tenant_id,
                user_id=current_user.id,
            )
        except TenantMembershipNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

        decision_rbac = authorize(membership.role, Permission.MODEL_GATEWAY_INVOKE)
        if not decision_rbac.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant role does not allow model invocation.",
            )

        try:
            governance_route = model_gateway.preview_route(
                agent_id=request.agent_id,
                provider=request.provider,
                model=request.model,
                capability=request.capability,
                metadata=request.metadata,
            )
        except ProviderNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

        estimated_output = request.max_tokens or 0
        estimated_cost = pricing_catalog.estimate(
            provider=governance_route.provider,
            model=governance_route.model or "unknown",
            input_tokens=0,
            output_tokens=estimated_output,
        )
        decision = await PlatformModelGovernanceService.authorize(
            session=session,
            tenant_id=request.tenant_id,
            provider=governance_route.provider,
            estimated_tokens=estimated_output,
            estimated_cost_usd=estimated_cost,
        )
        if not decision.allowed:
            code = (
                status.HTTP_403_FORBIDDEN
                if decision.reason == "provider_not_allowed"
                else status.HTTP_429_TOO_MANY_REQUESTS
            )
            raise HTTPException(
                status_code=code,
                detail={
                    "reason": decision.reason,
                    "remaining_tokens": decision.remaining_tokens,
                    "remaining_cost_usd": decision.remaining_cost_usd,
                },
            )
        allowed_providers = decision.allowed_providers

    try:
        result = await model_gateway.invoke(
            request=llm_request,
            agent_id=request.agent_id,
            provider=request.provider,
            model=request.model,
            capability=request.capability,
            allowed_providers=allowed_providers,
        )
    except ProviderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
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

    if request.tenant_id is not None and usage is not None:
        input_tokens = usage.input_tokens or 0
        output_tokens = usage.output_tokens or 0
        total_tokens = usage.total_tokens
        if total_tokens is None:
            total_tokens = input_tokens + output_tokens
        cost_usd = pricing_catalog.estimate(
            provider=result.response.provider,
            model=result.response.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        await PlatformModelGovernanceService.record_usage(
            session=session,
            tenant_id=request.tenant_id,
            provider=result.response.provider,
            model=result.response.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            request_id=str(request.metadata.get("request_id")) if request.metadata.get("request_id") else None,
            route_reason=result.route.reason,
        )

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
            fallback_providers=list(result.route.fallback_providers),
        ),
        attempted_providers=list(result.attempted_providers),
    )

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.model_gateway.bootstrap import model_gateway
from app.model_gateway.registry import ProviderNotFoundError
from app.production_ai.runtime import ProductionAgentRuntime
from app.schemas.production_ai import (
    GuardrailStageResponse,
    ProductionReadinessResponse,
    ProductionRuntimeRequest,
    ProductionRuntimeResponse,
    RuntimeEvaluationResponse,
)
from app.security.rbac import Permission, authorize
from app.services.guarded_execution_service import guarded_execution_service
from app.services.platform_v4_model_governance_service import ModelPricingCatalog, PlatformModelGovernanceService
from app.services.tenant_service import TenantMembershipNotFoundError, TenantService


router = APIRouter(prefix="/production-ai", tags=["Production Agentic AI"])
runtime = ProductionAgentRuntime(gateway=model_gateway)
pricing = ModelPricingCatalog.from_environment()


@router.get("/readiness", response_model=ProductionReadinessResponse)
async def readiness(current_user: CurrentUser) -> ProductionReadinessResponse:
    del current_user
    return ProductionReadinessResponse(
        status="ready",
        capabilities={
            "multi_provider_gateway": True,
            "unified_agent_runtime": True,
            "guardrails": True,
            "evaluation_gates": True,
            "ai_observability": True,
            "reliability_scalability": True,
            "cost_aware_routing": True,
        },
        providers=[item.name for item in model_gateway.registry.descriptors()],
    )


@router.post("/runtime/execute", response_model=ProductionRuntimeResponse)
async def execute_runtime(
    body: ProductionRuntimeRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ProductionRuntimeResponse:
    try:
        membership = await TenantService.get_membership(session=session, tenant_id=body.tenant_id, user_id=current_user.id)
    except TenantMembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if not authorize(membership.role, Permission.MODEL_GATEWAY_INVOKE).allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant role cannot execute production AI runtime.")

    budget = await PlatformModelGovernanceService.ensure_budget(session=session, tenant_id=body.tenant_id)
    allowed_for_routing = list(budget.allowed_providers) if budget.allowed_providers else None
    try:
        route = model_gateway.preview_route(
            agent_id=body.agent_id,
            provider=body.provider,
            model=body.model,
            capability=body.capability,
            metadata={
                "routing_mode": "cost",
                "estimated_output_tokens": body.max_tokens or 512,
                "allowed_providers": allowed_for_routing,
            },
        )
    except ProviderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    estimated_cost = pricing.estimate(provider=route.provider, model=route.model or "unknown", input_tokens=0, output_tokens=body.max_tokens or 0)
    governance = await PlatformModelGovernanceService.authorize(
        session=session,
        tenant_id=body.tenant_id,
        provider=route.provider,
        estimated_tokens=body.max_tokens or 0,
        estimated_cost_usd=estimated_cost,
    )
    if not governance.allowed:
        code = status.HTTP_403_FORBIDDEN if governance.reason == "provider_not_allowed" else status.HTTP_429_TOO_MANY_REQUESTS
        raise HTTPException(status_code=code, detail=governance.reason)

    async def tool_runner(source: str, name: str, arguments: dict):
        call = next(item for item in body.tool_calls if item.source == source and item.name == name and item.arguments == arguments)
        if source == "mcp":
            result = await guarded_execution_service.execute_mcp(
                session=session, user_id=current_user.id, qualified_name=name, arguments=arguments,
                workflow_id=body.agent_id, request_content=body.prompt, approval_granted=call.approval_granted,
            )
        else:
            result = await guarded_execution_service.execute_internal(
                session=session, user_id=current_user.id, tool_name=name, arguments=arguments,
                workflow_id=body.agent_id, request_content=body.prompt, approval_granted=call.approval_granted,
            )
        if not result.executed:
            raise PermissionError(result.evaluation.reason)
        value = result.result
        return value.model_dump() if hasattr(value, "model_dump") else value

    try:
        result = await runtime.execute(
            agent_id=body.agent_id,
            prompt=body.prompt,
            provider=body.provider,
            model=body.model,
            capability=body.capability,
            context=body.context,
            business_rules=body.business_rules,
            tool_calls=[(item.source, item.name, item.arguments) for item in body.tool_calls],
            tool_runner=tool_runner if body.tool_calls else None,
            allowed_providers=governance.allowed_providers,
            max_tokens=body.max_tokens,
            max_latency_ms=body.max_latency_ms,
            max_cost_usd=body.max_cost_usd,
            estimated_cost=lambda provider, model, inp, out: pricing.estimate(provider=provider, model=model, input_tokens=inp, output_tokens=out),
            idempotency_key=(f"{body.tenant_id}:{body.agent_id}:{body.idempotency_key}" if body.idempotency_key else None),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if not result.cache_hit:
        await PlatformModelGovernanceService.record_usage(
            session=session,
            tenant_id=body.tenant_id,
            provider=result.provider,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
            cost_usd=result.cost_usd,
            request_id=body.idempotency_key,
            route_reason="production_runtime",
        )

    return ProductionRuntimeResponse(
        content=result.content,
        provider=result.provider,
        model=result.model,
        latency_ms=result.latency_ms,
        cost_usd=result.cost_usd,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        total_tokens=result.total_tokens,
        attempted_providers=list(result.attempted_providers),
        tool_results=list(result.tool_results),
        cache_hit=result.cache_hit,
        input_guardrail=GuardrailStageResponse(decision=result.input_guardrail.decision.value, reasons=list(result.input_guardrail.reasons)),
        output_guardrail=GuardrailStageResponse(decision=result.output_guardrail.decision.value, reasons=list(result.output_guardrail.reasons)),
        evaluation=RuntimeEvaluationResponse(outcome=result.evaluation.outcome.value, score=result.evaluation.score, reasons=list(result.evaluation.reasons)),
    )

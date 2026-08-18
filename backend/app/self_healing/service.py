from __future__ import annotations
from app.self_healing.executor import replacement_execution_adapter
from app.self_healing.handoff import context_handoff_service
from app.self_healing.health_state import agent_runtime_health_store
from app.self_healing.idempotency import failover_idempotency_store
from app.self_healing.persistence import failover_checkpoint_store
from app.self_healing.policy import self_healing_policy
from app.self_healing.rejoin import agent_rejoin_policy
from app.self_healing.routing import health_aware_agent_router
from app.self_healing.schemas import FailoverRequest, FailoverResult

class SelfHealingService:
    async def record_failure(self, agent_id: str, *, error: str | None = None):
        return await agent_runtime_health_store.record_failure(agent_id, error=error)
    async def record_recovery(self, agent_id: str):
        return await agent_runtime_health_store.record_recovery(agent_id)
    async def rejoin_allowed(self, agent_id: str) -> bool:
        return agent_rejoin_policy.allowed(await agent_runtime_health_store.get(agent_id))
    async def failover(self, request: FailoverRequest, *, trace_id: str | None = None) -> FailoverResult:
        existing = await failover_idempotency_store.get(request.idempotency_key)
        if existing is not None: return existing

        decision = await health_aware_agent_router.select(request.capability_query, allow_degraded=request.allow_degraded)
        selected = decision.selected_agent_id
        if selected == request.failed_agent_id:
            selected = next((c.agent_id for c in decision.candidates if c.routable and c.agent_id != request.failed_agent_id), None)

        policy_decision, risk, executable, reason = self_healing_policy.evaluate(request, selected)
        if not executable:
            result = FailoverResult(status="blocked", failed_agent_id=request.failed_agent_id, replacement_agent_id=selected, idempotency_key=request.idempotency_key, evidence={"policy_decision": policy_decision, "risk": risk, "reason": reason})
            await failover_checkpoint_store.save(request.idempotency_key, {"stage": "blocked", "result": result.model_dump(mode="json")})
            await failover_idempotency_store.put(request.idempotency_key, result)
            return result

        try:
            handoff = context_handoff_service.build(request, target_agent_id=selected, trace_id=trace_id)
            await failover_checkpoint_store.save(request.idempotency_key, {"stage": "handoff_ready", "handoff": handoff})
            execution = await replacement_execution_adapter.execute(handoff)
            verification = await replacement_execution_adapter.verify(target_agent_id=selected, execution_result=execution)
            if not verification.get("healthy"):
                raise RuntimeError(f"Replacement verification failed: {verification}")
            result = FailoverResult(status="completed", failed_agent_id=request.failed_agent_id, replacement_agent_id=selected, idempotency_key=request.idempotency_key, verification=verification, evidence={"routing_reason": decision.reason, "policy_decision": policy_decision, "risk": risk, "handoff": handoff, "execution": execution})
            await failover_checkpoint_store.save(request.idempotency_key, {"stage": "completed", "result": result.model_dump(mode="json")})
            await failover_idempotency_store.put(request.idempotency_key, result)
            return result
        except Exception as exc:
            result = FailoverResult(status="failed", failed_agent_id=request.failed_agent_id, replacement_agent_id=selected, idempotency_key=request.idempotency_key, error=str(exc), evidence={"fail_closed": True})
            await failover_checkpoint_store.save(request.idempotency_key, {"stage": "failed", "result": result.model_dump(mode="json")})
            await failover_idempotency_store.put(request.idempotency_key, result)
            return result

self_healing_service = SelfHealingService()

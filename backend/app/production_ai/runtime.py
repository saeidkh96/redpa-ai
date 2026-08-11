from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Awaitable, Callable

from app.model_gateway.contracts import LLMCapability, LLMMessage, LLMRequest
from app.model_gateway.gateway import ModelGateway
from app.production_ai.evaluator import RuntimeEvaluation, RuntimeEvaluator
from app.production_ai.guardrails import ContentGuardrailDecision, ContentGuardrailResult, ProductionGuardrailPipeline
from app.production_ai.reliability import AsyncConcurrencyGate, InMemoryIdempotencyStore
from app.production_ai.telemetry import AI_GUARDRAIL_DECISIONS, AI_RUNTIME_COST, AI_RUNTIME_LATENCY, AI_RUNTIME_REQUESTS, AI_TOOL_CALLS

ToolRunner = Callable[[str, str, dict], Awaitable[object]]


@dataclass(frozen=True, slots=True)
class ProductionRuntimeResult:
    content: str
    provider: str
    model: str
    latency_ms: float
    cost_usd: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    attempted_providers: tuple[str, ...]
    input_guardrail: ContentGuardrailResult
    output_guardrail: ContentGuardrailResult
    evaluation: RuntimeEvaluation
    tool_results: tuple[str, ...]
    cache_hit: bool = False


class ProductionAgentRuntime:
    def __init__(self, *, gateway: ModelGateway, guardrails: ProductionGuardrailPipeline | None = None, evaluator: RuntimeEvaluator | None = None, concurrency_limit: int = 32) -> None:
        self.gateway = gateway
        self.guardrails = guardrails or ProductionGuardrailPipeline()
        self.evaluator = evaluator or RuntimeEvaluator()
        self.gate = AsyncConcurrencyGate(concurrency_limit)
        self.idempotency = InMemoryIdempotencyStore()

    async def execute(self, *, agent_id: str, prompt: str, provider: str | None = None, model: str | None = None, capability: LLMCapability = LLMCapability.CHAT, context: list[str] | None = None, business_rules: list[str] | None = None, tool_calls: list[tuple[str, str, dict]] | None = None, tool_runner: ToolRunner | None = None, allowed_providers: set[str] | frozenset[str] | None = None, max_tokens: int | None = None, max_latency_ms: float | None = None, max_cost_usd: float | None = None, estimated_cost: Callable[[str, str, int, int], float] | None = None, idempotency_key: str | None = None) -> ProductionRuntimeResult:
        if idempotency_key:
            cached = self.idempotency.get(idempotency_key)
            if cached is not None:
                return replace(cached, cache_hit=True)
        input_guard = self.guardrails.evaluate_input(prompt)
        AI_GUARDRAIL_DECISIONS.labels(stage="input", decision=input_guard.decision.value).inc()
        if input_guard.decision in {ContentGuardrailDecision.BLOCK, ContentGuardrailDecision.REVIEW}:
            raise PermissionError(f"input_guardrail:{input_guard.decision.value}:{','.join(input_guard.reasons)}")

        tool_results: list[str] = []
        if tool_calls:
            if tool_runner is None:
                raise RuntimeError("tool_runner is required when tool_calls are provided")
            for source, name, arguments in tool_calls:
                try:
                    result = await tool_runner(source, name, arguments)
                    tool_results.append(f"{name}: {result}")
                    AI_TOOL_CALLS.labels(source=source, status="success").inc()
                except Exception as exc:
                    AI_TOOL_CALLS.labels(source=source, status="failed").inc()
                    raise RuntimeError(f"Tool call failed: {name}: {exc}") from exc

        messages: list[LLMMessage] = []
        if business_rules:
            messages.append(LLMMessage(role="system", content="Business rules:\n- " + "\n- ".join(business_rules)))
        if context:
            messages.append(LLMMessage(role="system", content="Data context:\n" + "\n\n".join(context)))
        if tool_results:
            messages.append(LLMMessage(role="system", content="Tool results:\n" + "\n".join(tool_results)))
        messages.append(LLMMessage(role="user", content=input_guard.content))

        started = time.perf_counter()
        async with self.gate:
            result = await self.gateway.invoke(
                request=LLMRequest(messages=tuple(messages), model=model, max_tokens=max_tokens, metadata={"routing_mode": "cost", "agent_id": agent_id}),
                agent_id=agent_id,
                provider=provider,
                model=model,
                capability=capability,
                allowed_providers=allowed_providers,
            )
        latency_ms = (time.perf_counter() - started) * 1000.0
        usage = result.response.usage
        inp = usage.input_tokens or 0 if usage else 0
        out = usage.output_tokens or 0 if usage else 0
        cost = estimated_cost(result.response.provider, result.response.model, inp, out) if estimated_cost else 0.0
        output_guard = self.guardrails.evaluate_output(result.response.content)
        AI_GUARDRAIL_DECISIONS.labels(stage="output", decision=output_guard.decision.value).inc()
        evaluation = self.evaluator.evaluate(content=output_guard.content, latency_ms=latency_ms, cost_usd=cost, max_latency_ms=max_latency_ms, max_cost_usd=max_cost_usd)
        AI_RUNTIME_REQUESTS.labels(agent=agent_id, outcome=evaluation.outcome.value).inc()
        AI_RUNTIME_LATENCY.labels(agent=agent_id, provider=result.response.provider).observe(latency_ms / 1000.0)
        AI_RUNTIME_COST.labels(agent=agent_id, provider=result.response.provider, model=result.response.model).inc(cost)
        final = ProductionRuntimeResult(output_guard.content, result.response.provider, result.response.model, latency_ms, cost, inp, out, (usage.total_tokens if usage and usage.total_tokens is not None else inp + out), result.attempted_providers, input_guard, output_guard, evaluation, tuple(tool_results))
        if idempotency_key:
            self.idempotency.put(idempotency_key, final)
        return final

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from prometheus_client import Counter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.contracts import EventEnvelope
from app.models.platform_v4_control import PlatformModelBudget, PlatformModelUsage
from app.services.event_outbox_service import EventOutboxService


MODEL_GOVERNANCE_DENIED_TOTAL = Counter(
    "redpa_model_governance_denied_total",
    "Model requests denied by v4 governance.",
    ("reason", "provider"),
)
MODEL_GOVERNANCE_USAGE_TOKENS_TOTAL = Counter(
    "redpa_model_governance_usage_tokens_total",
    "Model tokens recorded by v4 governance.",
    ("provider", "model"),
)
MODEL_GOVERNANCE_COST_USD_TOTAL = Counter(
    "redpa_model_governance_cost_usd_total",
    "Model cost in USD recorded by v4 governance.",
    ("provider", "model"),
)


class ModelGovernanceDeniedError(PermissionError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class GovernanceDecision:
    allowed: bool
    reason: str
    remaining_tokens: int
    remaining_cost_usd: float
    allowed_providers: frozenset[str] | None


class ModelPricingCatalog:
    """Simple provider/model pricing catalog loaded from environment.

    MODEL_GATEWAY_PRICING_JSON format:
    {
      "openai-compatible:gpt-4o-mini": {"input_per_1k": 0.00015, "output_per_1k": 0.0006},
      "ollama:*": {"input_per_1k": 0.0, "output_per_1k": 0.0}
    }
    """

    def __init__(self, entries: dict[str, dict[str, float]] | None = None) -> None:
        self._entries = entries or {}

    @classmethod
    def from_environment(cls) -> "ModelPricingCatalog":
        raw = os.getenv("MODEL_GATEWAY_PRICING_JSON", "").strip()
        if not raw:
            return cls()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("MODEL_GATEWAY_PRICING_JSON is not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("MODEL_GATEWAY_PRICING_JSON must be an object.")

        entries: dict[str, dict[str, float]] = {}
        for key, value in payload.items():
            if not isinstance(value, dict):
                continue
            entries[str(key)] = {
                "input_per_1k": float(value.get("input_per_1k", 0.0)),
                "output_per_1k": float(value.get("output_per_1k", 0.0)),
            }
        return cls(entries)

    def estimate(
        self,
        *,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        entry = self._entries.get(f"{provider}:{model}") or self._entries.get(f"{provider}:*")
        if entry is None:
            return 0.0
        return round(
            max(input_tokens, 0) / 1000.0 * entry["input_per_1k"]
            + max(output_tokens, 0) / 1000.0 * entry["output_per_1k"],
            8,
        )


def current_period_key(now: datetime | None = None) -> str:
    value = now or datetime.now(timezone.utc)
    return value.strftime("%Y-%m")


class PlatformModelGovernanceService:
    DEFAULT_TOKEN_LIMIT = 1_000_000
    DEFAULT_COST_LIMIT_USD = 25.0

    @classmethod
    async def get_budget(
        cls,
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        period_key: str | None = None,
        lock: bool = False,
    ) -> PlatformModelBudget | None:
        query = select(PlatformModelBudget).where(
            PlatformModelBudget.tenant_id == tenant_id,
            PlatformModelBudget.period_key == (period_key or current_period_key()),
        )
        if lock:
            query = query.with_for_update()
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def ensure_budget(
        cls,
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        commit: bool = False,
    ) -> PlatformModelBudget:
        budget = await cls.get_budget(session=session, tenant_id=tenant_id, lock=True)
        if budget is not None:
            return budget
        budget = PlatformModelBudget(
            tenant_id=tenant_id,
            period_key=current_period_key(),
            monthly_token_limit=cls.DEFAULT_TOKEN_LIMIT,
            monthly_cost_limit_usd=cls.DEFAULT_COST_LIMIT_USD,
            allowed_providers=[],
        )
        session.add(budget)
        await session.flush()
        if commit:
            await session.commit()
            await session.refresh(budget)
        return budget

    @classmethod
    async def upsert_budget(
        cls,
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        monthly_token_limit: int,
        monthly_cost_limit_usd: float,
        allowed_providers: list[str],
        actor_id: uuid.UUID,
    ) -> PlatformModelBudget:
        if monthly_token_limit <= 0 or monthly_cost_limit_usd <= 0:
            raise ValueError("Budget limits must be positive.")

        budget = await cls.get_budget(session=session, tenant_id=tenant_id, lock=True)
        if budget is None:
            budget = PlatformModelBudget(
                tenant_id=tenant_id,
                period_key=current_period_key(),
                monthly_token_limit=monthly_token_limit,
                monthly_cost_limit_usd=monthly_cost_limit_usd,
                allowed_providers=sorted(set(allowed_providers)),
            )
            session.add(budget)
        else:
            budget.monthly_token_limit = monthly_token_limit
            budget.monthly_cost_limit_usd = monthly_cost_limit_usd
            budget.allowed_providers = sorted(set(allowed_providers))

        await session.flush()
        await EventOutboxService.enqueue(
            session=session,
            event=EventEnvelope(
                event_type="platform.model_budget.updated",
                aggregate_type="model_budget",
                aggregate_id=str(budget.id),
                tenant_id=tenant_id,
                payload={
                    "period_key": budget.period_key,
                    "monthly_token_limit": budget.monthly_token_limit,
                    "monthly_cost_limit_usd": budget.monthly_cost_limit_usd,
                    "allowed_providers": budget.allowed_providers,
                    "actor_id": str(actor_id),
                },
            ),
            commit=False,
        )
        await session.commit()
        await session.refresh(budget)
        return budget

    @classmethod
    async def authorize(
        cls,
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        provider: str,
        estimated_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> GovernanceDecision:
        budget = await cls.ensure_budget(session=session, tenant_id=tenant_id)
        allowed_set = frozenset(budget.allowed_providers) if budget.allowed_providers else None

        reason = "allowed"
        allowed = True
        if allowed_set is not None and provider not in allowed_set:
            reason = "provider_not_allowed"
            allowed = False
        elif budget.used_tokens + max(estimated_tokens, 0) > budget.monthly_token_limit:
            reason = "token_budget_exceeded"
            allowed = False
        elif budget.used_cost_usd + max(estimated_cost_usd, 0.0) > budget.monthly_cost_limit_usd:
            reason = "cost_budget_exceeded"
            allowed = False

        if not allowed:
            MODEL_GOVERNANCE_DENIED_TOTAL.labels(reason=reason, provider=provider).inc()

        return GovernanceDecision(
            allowed=allowed,
            reason=reason,
            remaining_tokens=max(budget.monthly_token_limit - budget.used_tokens, 0),
            remaining_cost_usd=max(budget.monthly_cost_limit_usd - budget.used_cost_usd, 0.0),
            allowed_providers=allowed_set,
        )

    @classmethod
    async def record_usage(
        cls,
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cost_usd: float,
        request_id: str | None = None,
        route_reason: str | None = None,
    ) -> PlatformModelUsage:
        budget = await cls.ensure_budget(session=session, tenant_id=tenant_id)
        # Re-read under a row lock before mutating counters.
        budget = await cls.get_budget(session=session, tenant_id=tenant_id, lock=True) or budget

        safe_total = max(total_tokens, 0)
        safe_cost = max(cost_usd, 0.0)
        budget.used_tokens += safe_total
        budget.used_cost_usd += safe_cost

        usage = PlatformModelUsage(
            tenant_id=tenant_id,
            request_id=request_id,
            provider=provider,
            model=model,
            input_tokens=max(input_tokens, 0),
            output_tokens=max(output_tokens, 0),
            total_tokens=safe_total,
            cost_usd=safe_cost,
            route_reason=route_reason,
        )
        session.add(usage)
        await session.flush()

        await EventOutboxService.enqueue(
            session=session,
            event=EventEnvelope(
                event_type="platform.model_usage.recorded",
                aggregate_type="model_usage",
                aggregate_id=str(usage.id),
                tenant_id=tenant_id,
                payload={
                    "provider": provider,
                    "model": model,
                    "total_tokens": safe_total,
                    "cost_usd": safe_cost,
                    "request_id": request_id,
                },
            ),
            commit=False,
        )
        await session.commit()
        await session.refresh(usage)

        MODEL_GOVERNANCE_USAGE_TOKENS_TOTAL.labels(provider=provider, model=model).inc(safe_total)
        MODEL_GOVERNANCE_COST_USD_TOTAL.labels(provider=provider, model=model).inc(safe_cost)
        return usage

    @classmethod
    async def recent_usage(
        cls,
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        limit: int = 100,
    ) -> list[PlatformModelUsage]:
        result = await session.execute(
            select(PlatformModelUsage)
            .where(PlatformModelUsage.tenant_id == tenant_id)
            .order_by(PlatformModelUsage.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

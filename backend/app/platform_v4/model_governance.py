from __future__ import annotations
from dataclasses import dataclass, field
from .common import Registry

@dataclass(slots=True)
class ModelBudget:
    tenant_id: str
    monthly_token_limit: int = 1_000_000
    monthly_cost_limit_usd: float = 25.0
    used_tokens: int = 0
    used_cost_usd: float = 0.0
    allowed_providers: set[str] = field(default_factory=set)

    def can_spend(self, tokens: int, cost_usd: float, provider: str) -> tuple[bool, str]:
        if self.allowed_providers and provider not in self.allowed_providers:
            return False, "provider_not_allowed"
        if self.used_tokens + tokens > self.monthly_token_limit:
            return False, "token_budget_exceeded"
        if self.used_cost_usd + cost_usd > self.monthly_cost_limit_usd:
            return False, "cost_budget_exceeded"
        return True, "allowed"

    def charge(self, tokens: int, cost_usd: float) -> None:
        self.used_tokens += max(tokens, 0)
        self.used_cost_usd += max(cost_usd, 0.0)

class ModelGovernanceService:
    def __init__(self) -> None: self.budgets: Registry[ModelBudget] = Registry()
    def upsert(self, budget: ModelBudget) -> ModelBudget: return self.budgets.put(budget.tenant_id, budget)
    def snapshot(self) -> list[ModelBudget]: return self.budgets.list()

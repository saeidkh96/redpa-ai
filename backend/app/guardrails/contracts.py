from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class GuardrailDecision(str, enum.Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    DENY = "DENY"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class GuardrailAction:
    action: str
    resource: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.action.strip():
            raise ValueError("Guardrail action cannot be empty.")


@dataclass(frozen=True, slots=True)
class GuardrailRequest:
    action: GuardrailAction
    agent_id: str | None = None
    user_id: str | None = None
    workflow_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GuardrailEvaluation:
    decision: GuardrailDecision
    risk: RiskLevel
    reason: str
    matched_rules: tuple[str, ...] = ()
    policy_version: str = "unknown"
    source: str = "policy-service"

    @property
    def allowed(self) -> bool:
        return self.decision == GuardrailDecision.ALLOW

    @property
    def requires_review(self) -> bool:
        return self.decision == GuardrailDecision.REVIEW

    @property
    def denied(self) -> bool:
        return self.decision == GuardrailDecision.DENY

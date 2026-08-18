from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    passed: bool


def validate_v13_evidence(evidence: dict[str, Any]) -> list[Check]:
    checks = [
        Check("Stage 1 runtime signals", bool(evidence.get("stage1", {}).get("signals_persisted"))),
        Check("Stage 2 historical aggregation", bool(evidence.get("stage2", {}).get("history_used"))),
        Check("Stage 3 recommendation", bool(evidence.get("stage3", {}).get("recommendation_created"))),
        Check("Stage 4 risk scoring", bool(evidence.get("stage4", {}).get("risk_scored"))),
        Check(
            "Stage 5 human review boundary",
            bool(evidence.get("stage5", {}).get("high_risk_requires_review"))
            and not bool(evidence.get("stage5", {}).get("auto_applied")),
        ),
        Check("Stage 6 versioned proposals", bool(evidence.get("stage6", {}).get("version_incremented"))),
        Check("Stage 7 shadow evaluation", bool(evidence.get("stage7", {}).get("shadow_gate_enforced"))),
        Check(
            "Stage 8 explicit application",
            bool(evidence.get("stage8", {}).get("approved_before_apply"))
            and not bool(evidence.get("stage8", {}).get("auto_applied")),
        ),
        Check("Stage 9 rollback", bool(evidence.get("stage9", {}).get("rollback_verified"))),
    ]
    checks.append(Check("Stage 10 readiness gate", all(c.passed for c in checks)))
    return checks

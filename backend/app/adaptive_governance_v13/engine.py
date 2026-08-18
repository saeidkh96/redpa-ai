from __future__ import annotations

from statistics import mean

from app.adaptive_governance_v13.schemas import PolicyRecommendationResponse
from app.models.adaptive_governance_v13 import AdaptiveGovernanceSignal


class AdaptivePolicyRecommendationEngine:
    """Evidence-driven recommendation engine. It never applies policy changes."""

    @staticmethod
    def recommend(
        *,
        action: str,
        signals: list[AdaptiveGovernanceSignal],
    ) -> PolicyRecommendationResponse:
        if not signals:
            return PolicyRecommendationResponse(
                action=action,
                recommended_decision="ALLOW",
                recommended_risk="LOW",
                confidence=0.25,
                reasons=["No historical runtime evidence is available."],
                signal_count=0,
                failure_rate=0.0,
                incident_count=0,
                destructive_seen=False,
                auto_applied=False,
            )

        failure_rate = mean(max(s.failure_rate, s.error_rate) for s in signals)
        incident_count = sum(s.incident_count for s in signals)
        destructive_seen = any(s.destructive for s in signals)
        privileged_seen = any(s.write_access or s.handles_secrets for s in signals)
        external_seen = any(s.external_network for s in signals)

        score = 0
        reasons: list[str] = []

        if destructive_seen:
            score += 4
            reasons.append("Destructive runtime activity observed.")
        if privileged_seen:
            score += 3
            reasons.append("Write access or secret handling observed.")
        if external_seen:
            score += 1
            reasons.append("External network access observed.")
        if failure_rate >= 0.25:
            score += 4
            reasons.append("Historical failure/error rate is at least 25%.")
        elif failure_rate >= 0.10:
            score += 2
            reasons.append("Historical failure/error rate is elevated.")
        if incident_count >= 5:
            score += 3
            reasons.append("Repeated incidents observed.")
        elif incident_count >= 3:
            score += 2
            reasons.append("Multiple incidents observed.")

        if score >= 8:
            decision, risk = "DENY", "CRITICAL"
        elif score >= 4:
            decision, risk = "REVIEW", "HIGH"
        elif score >= 2:
            decision, risk = "REVIEW", "MEDIUM"
        else:
            decision, risk = "ALLOW", "LOW"

        sample_factor = min(len(signals) / 20.0, 1.0)
        confidence = round(min(0.99, 0.45 + sample_factor * 0.45 + min(score, 8) * 0.01), 2)

        if not reasons:
            reasons.append("Observed runtime evidence remains within low-risk thresholds.")

        return PolicyRecommendationResponse(
            action=action,
            recommended_decision=decision,
            recommended_risk=risk,
            confidence=confidence,
            reasons=reasons,
            signal_count=len(signals),
            failure_rate=round(failure_rate, 4),
            incident_count=incident_count,
            destructive_seen=destructive_seen,
            auto_applied=False,
        )


adaptive_policy_engine = AdaptivePolicyRecommendationEngine()

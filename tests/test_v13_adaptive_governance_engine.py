from __future__ import annotations

from types import SimpleNamespace

from app.adaptive_governance_v13.engine import AdaptivePolicyRecommendationEngine


def signal(**overrides):
    data = {
        "failure_rate": 0.0,
        "error_rate": 0.0,
        "incident_count": 0,
        "destructive": False,
        "write_access": False,
        "handles_secrets": False,
        "external_network": False,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_v13_low_risk_evidence_can_recommend_allow():
    result = AdaptivePolicyRecommendationEngine.recommend(
        action="read_data",
        signals=[signal(), signal()],
    )
    assert result.recommended_decision == "ALLOW"
    assert result.recommended_risk == "LOW"
    assert result.auto_applied is False


def test_v13_destructive_high_failure_recommends_deny():
    result = AdaptivePolicyRecommendationEngine.recommend(
        action="restart_cluster",
        signals=[
            signal(
                destructive=True,
                write_access=True,
                failure_rate=0.40,
                incident_count=6,
            )
        ],
    )
    assert result.recommended_decision == "DENY"
    assert result.recommended_risk == "CRITICAL"
    assert result.auto_applied is False


def test_v13_recommendation_is_evidence_driven():
    result = AdaptivePolicyRecommendationEngine.recommend(
        action="external_query",
        signals=[
            signal(external_network=True, failure_rate=0.15, incident_count=3),
            signal(external_network=True, failure_rate=0.10, incident_count=1),
        ],
    )
    assert result.signal_count == 2
    assert result.failure_rate >= 0.10
    assert result.recommended_decision in {"REVIEW", "DENY"}

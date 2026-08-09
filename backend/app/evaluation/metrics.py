from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.models.evaluation import EvaluationMetric
from app.schemas.evaluation import EvaluationInput

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    return {token.lower() for token in _TOKEN_RE.findall(text) if len(token) > 1}


def _overlap_score(left: str | None, right: str | None) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    union = len(left_tokens | right_tokens)
    return len(left_tokens & right_tokens) / union if union else 0.0


def _clamp(score: float) -> float:
    if math.isnan(score) or math.isinf(score):
        return 0.0
    return max(0.0, min(1.0, float(score)))


@dataclass(slots=True)
class EvaluationMetricResult:
    score: float
    details: dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> "EvaluationMetricResult":
        return EvaluationMetricResult(score=_clamp(self.score), details=self.details)


class BaseEvaluationMetric(ABC):
    name: EvaluationMetric

    @abstractmethod
    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        raise NotImplementedError


class TaskSuccessMetric(BaseEvaluationMetric):
    name = EvaluationMetric.TASK_SUCCESS

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        if evaluation_input.success is None:
            return EvaluationMetricResult(0.0, {"reason": "success signal was not provided"})
        return EvaluationMetricResult(1.0 if evaluation_input.success else 0.0, {"success": evaluation_input.success})


class RoutingAccuracyMetric(BaseEvaluationMetric):
    name = EvaluationMetric.ROUTING_ACCURACY

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        expected = (evaluation_input.expected_route or "").strip().lower()
        actual = (evaluation_input.actual_route or "").strip().lower()
        if not expected or not actual:
            return EvaluationMetricResult(0.0, {"expected_route": expected or None, "actual_route": actual or None, "reason": "expected and actual routes are required"})
        return EvaluationMetricResult(1.0 if expected == actual else 0.0, {"expected_route": expected, "actual_route": actual})


class ToolSelectionAccuracyMetric(BaseEvaluationMetric):
    name = EvaluationMetric.TOOL_SELECTION_ACCURACY

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        expected = {tool.strip().lower() for tool in evaluation_input.expected_tools if tool.strip()}
        actual = {tool.strip().lower() for tool in evaluation_input.actual_tools if tool.strip()}
        if not expected and not actual:
            return EvaluationMetricResult(1.0, {"precision": 1.0, "recall": 1.0, "f1": 1.0, "expected_tools": [], "actual_tools": []})
        if not expected or not actual:
            return EvaluationMetricResult(0.0, {"precision": 0.0, "recall": 0.0, "f1": 0.0, "expected_tools": sorted(expected), "actual_tools": sorted(actual)})
        tp = len(expected & actual)
        precision = tp / len(actual)
        recall = tp / len(expected)
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        return EvaluationMetricResult(f1, {"precision": precision, "recall": recall, "f1": f1, "expected_tools": sorted(expected), "actual_tools": sorted(actual)})


class ResponseRelevanceMetric(BaseEvaluationMetric):
    name = EvaluationMetric.RESPONSE_RELEVANCE

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        return EvaluationMetricResult(_overlap_score(evaluation_input.request_text, evaluation_input.response_text), {"method": "lexical_jaccard_baseline"})


class RagFaithfulnessMetric(BaseEvaluationMetric):
    name = EvaluationMetric.RAG_FAITHFULNESS

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        claims = [claim.strip() for claim in evaluation_input.claims if claim.strip()]
        contexts = [context.strip() for context in evaluation_input.contexts if context.strip()]
        if not claims or not contexts:
            return EvaluationMetricResult(0.0, {"supported_claims": 0, "claim_count": len(claims), "context_count": len(contexts), "reason": "claims and contexts are required"})
        threshold = 0.15
        claim_scores = [max(_overlap_score(claim, context) for context in contexts) for claim in claims]
        supported = sum(score >= threshold for score in claim_scores)
        return EvaluationMetricResult(supported / len(claims), {"supported_claims": supported, "claim_count": len(claims), "support_threshold": threshold, "claim_support_scores": claim_scores, "method": "lexical_support_baseline"})


class ContextRelevanceMetric(BaseEvaluationMetric):
    name = EvaluationMetric.CONTEXT_RELEVANCE

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        contexts = [context for context in evaluation_input.contexts if context.strip()]
        if not evaluation_input.request_text or not contexts:
            return EvaluationMetricResult(0.0, {"context_count": len(contexts), "reason": "request_text and contexts are required"})
        scores = [_overlap_score(evaluation_input.request_text, context) for context in contexts]
        return EvaluationMetricResult(sum(scores) / len(scores), {"context_count": len(contexts), "context_scores": scores, "method": "mean_lexical_jaccard_baseline"})


class LatencyMetric(BaseEvaluationMetric):
    name = EvaluationMetric.LATENCY

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        latency, target = evaluation_input.latency_ms, evaluation_input.latency_target_ms
        if latency is None or target is None:
            return EvaluationMetricResult(0.0, {"reason": "latency_ms and latency_target_ms are required"})
        score = 1.0 if latency <= target else target / latency
        return EvaluationMetricResult(score, {"latency_ms": latency, "target_ms": target})


class TokenUsageMetric(BaseEvaluationMetric):
    name = EvaluationMetric.TOKEN_USAGE

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        total, budget = evaluation_input.total_tokens, evaluation_input.token_budget
        if total is None or budget is None:
            return EvaluationMetricResult(0.0, {"reason": "token usage and token_budget are required"})
        score = 1.0 if total <= budget else budget / total
        return EvaluationMetricResult(score, {"input_tokens": evaluation_input.input_tokens or 0, "output_tokens": evaluation_input.output_tokens or 0, "total_tokens": total, "token_budget": budget})


class CostMetric(BaseEvaluationMetric):
    name = EvaluationMetric.COST

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        cost, budget = evaluation_input.cost_usd, evaluation_input.cost_budget_usd
        if cost is None or budget is None:
            return EvaluationMetricResult(0.0, {"reason": "cost_usd and cost_budget_usd are required"})
        score = 1.0 if cost <= budget else budget / cost
        return EvaluationMetricResult(score, {"cost_usd": cost, "cost_budget_usd": budget})


class EvaluationMetricRegistry:
    def __init__(self) -> None:
        metrics: list[BaseEvaluationMetric] = [
            TaskSuccessMetric(), RoutingAccuracyMetric(), ToolSelectionAccuracyMetric(),
            ResponseRelevanceMetric(), RagFaithfulnessMetric(), ContextRelevanceMetric(),
            LatencyMetric(), TokenUsageMetric(), CostMetric(),
        ]
        self._metrics = {metric.name: metric for metric in metrics}

    def get(self, metric: EvaluationMetric) -> BaseEvaluationMetric:
        try:
            return self._metrics[metric]
        except KeyError as exc:
            raise KeyError(f"Unsupported evaluation metric: {metric.value}") from exc

    def evaluate(self, *, metric: EvaluationMetric, evaluation_input: EvaluationInput) -> EvaluationMetricResult:
        return self.get(metric).evaluate(evaluation_input).normalized()

    def supported_metrics(self) -> list[EvaluationMetric]:
        return list(self._metrics.keys())

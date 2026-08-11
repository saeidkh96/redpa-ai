from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EvaluationOutcome(StrEnum):
    PASS = "pass"
    RETRY = "retry"
    HUMAN_REVIEW = "human_review"
    BLOCK = "block"


@dataclass(frozen=True, slots=True)
class RuntimeEvaluation:
    outcome: EvaluationOutcome
    score: float
    reasons: tuple[str, ...]


class RuntimeEvaluator:
    """
    Production evaluation gate for agent-runtime responses.

    Outcomes
    --------
    PASS
        The response satisfies configured runtime and quality budgets.

    RETRY
        A recoverable runtime target was missed and another attempt may help.

    HUMAN_REVIEW
        One or more significant runtime-policy violations occurred and
        operator review is preferable to automatic continuation.

    BLOCK
        The execution violated multiple severe runtime constraints or
        produced a critically low evaluation score.
    """

    PASS_THRESHOLD = 0.80
    RETRY_THRESHOLD = 0.60
    HUMAN_REVIEW_THRESHOLD = 0.40

    def evaluate(
        self,
        *,
        content: str,
        latency_ms: float,
        cost_usd: float,
        max_latency_ms: float | None = None,
        max_cost_usd: float | None = None,
    ) -> RuntimeEvaluation:
        content = content.strip()

        if not content:
            return RuntimeEvaluation(
                outcome=EvaluationOutcome.RETRY,
                score=0.0,
                reasons=("empty_response",),
            )

        reasons: list[str] = []
        score = 1.0

        latency_ratio: float | None = None
        cost_ratio: float | None = None

        # ------------------------------------------------------------
        # Latency budget
        # ------------------------------------------------------------

        if (
            max_latency_ms is not None
            and max_latency_ms > 0
            and latency_ms > max_latency_ms
        ):
            latency_ratio = latency_ms / max_latency_ms
            reasons.append("latency_target_missed")

            if latency_ratio >= 10.0:
                score -= 0.60
                reasons.append(
                    "latency_target_severely_exceeded"
                )

            elif latency_ratio >= 4.0:
                score -= 0.40
                reasons.append(
                    "latency_target_significantly_exceeded"
                )

            elif latency_ratio >= 2.0:
                score -= 0.30
                reasons.append(
                    "latency_target_exceeded"
                )

            else:
                score -= 0.20

        # ------------------------------------------------------------
        # Cost budget
        # ------------------------------------------------------------

        if (
            max_cost_usd is not None
            and max_cost_usd > 0
            and cost_usd > max_cost_usd
        ):
            cost_ratio = cost_usd / max_cost_usd
            reasons.append("cost_target_missed")

            if cost_ratio >= 10.0:
                score -= 0.50
                reasons.append(
                    "cost_target_severely_exceeded"
                )

            elif cost_ratio >= 4.0:
                score -= 0.40
                reasons.append(
                    "cost_target_significantly_exceeded"
                )

            elif cost_ratio >= 2.0:
                score -= 0.30
                reasons.append(
                    "cost_target_exceeded"
                )

            else:
                score -= 0.20

        score = max(
            0.0,
            min(1.0, score),
        )

        severe_latency = (
            latency_ratio is not None
            and latency_ratio >= 10.0
        )

        severe_cost = (
            cost_ratio is not None
            and cost_ratio >= 10.0
        )

        significant_latency = (
            latency_ratio is not None
            and latency_ratio >= 4.0
        )

        significant_cost = (
            cost_ratio is not None
            and cost_ratio >= 4.0
        )

        both_budgets_missed = (
            latency_ratio is not None
            and cost_ratio is not None
        )

        # ------------------------------------------------------------
        # Hard escalation rules
        # ------------------------------------------------------------

        # Only multiple severe violations cause an automatic block.
        if severe_latency and severe_cost:
            return RuntimeEvaluation(
                outcome=EvaluationOutcome.BLOCK,
                score=score,
                reasons=tuple(
                    reasons
                    + [
                        "multiple_severe_runtime_budget_violations",
                    ]
                ),
            )

        # A single severe budget violation requires human review,
        # but does not automatically block the execution.
        if severe_latency or severe_cost:
            return RuntimeEvaluation(
                outcome=EvaluationOutcome.HUMAN_REVIEW,
                score=score,
                reasons=tuple(
                    reasons
                    + [
                        "severe_runtime_budget_violation",
                    ]
                ),
            )

        # Multiple significant misses also require human review.
        if (
            both_budgets_missed
            and (
                significant_latency
                or significant_cost
            )
        ):
            return RuntimeEvaluation(
                outcome=EvaluationOutcome.HUMAN_REVIEW,
                score=score,
                reasons=tuple(
                    reasons
                    + [
                        "multiple_runtime_targets_missed",
                    ]
                ),
            )

        # ------------------------------------------------------------
        # Score-based evaluation gate
        # ------------------------------------------------------------

        if score < self.HUMAN_REVIEW_THRESHOLD:
            return RuntimeEvaluation(
                outcome=EvaluationOutcome.BLOCK,
                score=score,
                reasons=tuple(
                    reasons
                    + [
                        "evaluation_score_below_block_threshold",
                    ]
                ),
            )

        if score < self.RETRY_THRESHOLD:
            return RuntimeEvaluation(
                outcome=EvaluationOutcome.HUMAN_REVIEW,
                score=score,
                reasons=tuple(
                    reasons
                    + [
                        "evaluation_score_requires_human_review",
                    ]
                ),
            )

        if score < self.PASS_THRESHOLD:
            return RuntimeEvaluation(
                outcome=EvaluationOutcome.RETRY,
                score=score,
                reasons=tuple(
                    reasons
                    + [
                        "evaluation_score_requires_retry",
                    ]
                ),
            )

        return RuntimeEvaluation(
            outcome=EvaluationOutcome.PASS,
            score=score,
            reasons=tuple(
                reasons
                or [
                    "quality_gate_passed",
                ]
            ),
        )
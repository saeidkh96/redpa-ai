from __future__ import annotations

from app.models.evaluation import EvaluationRun
from app.schemas.evaluation_regression import (
    EvaluationRegressionRequest,
    EvaluationRegressionResponse,
    QualityGateRequest,
    QualityGateResponse,
    RegressionMetricDelta,
)


class EvaluationRegressionService:
    @staticmethod
    def _score_map(run: EvaluationRun) -> dict[str, float]:
        return {
            str(item.metric): float(item.score)
            for item in run.results
        }

    @classmethod
    def compare(
        cls,
        *,
        baseline: EvaluationRun,
        candidate: EvaluationRun,
        request: EvaluationRegressionRequest,
    ) -> EvaluationRegressionResponse:
        baseline_score = float(baseline.aggregate_score or 0.0)
        candidate_score = float(candidate.aggregate_score or 0.0)
        aggregate_delta = candidate_score - baseline_score

        baseline_metrics = cls._score_map(baseline)
        candidate_metrics = cls._score_map(candidate)
        metric_names = sorted(set(baseline_metrics) | set(candidate_metrics))

        metric_deltas: list[RegressionMetricDelta] = []
        regressed_metrics: list[str] = []

        for metric in metric_names:
            baseline_value = baseline_metrics.get(metric)
            candidate_value = candidate_metrics.get(metric)

            delta = (
                candidate_value - baseline_value
                if baseline_value is not None and candidate_value is not None
                else None
            )
            regressed = (
                baseline_value is not None
                and (
                    candidate_value is None
                    or (
                        delta is not None
                        and delta < -request.max_metric_drop
                    )
                )
            )

            if regressed:
                regressed_metrics.append(metric)

            metric_deltas.append(
                RegressionMetricDelta(
                    metric=metric,
                    baseline_score=baseline_value,
                    candidate_score=candidate_value,
                    delta=delta,
                    regressed=regressed,
                )
            )

        regression_detected = (
            aggregate_delta < -request.max_aggregate_drop
            or bool(regressed_metrics)
        )

        return EvaluationRegressionResponse(
            baseline_run_id=baseline.id,
            candidate_run_id=candidate.id,
            baseline_score=baseline_score,
            candidate_score=candidate_score,
            aggregate_delta=aggregate_delta,
            metric_deltas=metric_deltas,
            regressed_metrics=regressed_metrics,
            regression_detected=regression_detected,
        )

    @classmethod
    def quality_gate(
        cls,
        *,
        baseline: EvaluationRun,
        candidate: EvaluationRun,
        request: QualityGateRequest,
    ) -> QualityGateResponse:
        regression = cls.compare(
            baseline=baseline,
            candidate=candidate,
            request=request,
        )
        reasons: list[str] = []

        if regression.aggregate_delta < -request.max_aggregate_drop:
            reasons.append("aggregate_score_regression")

        if regression.regressed_metrics:
            reasons.append(
                "metric_regressions:"
                + ",".join(regression.regressed_metrics)
            )

        if request.require_candidate_pass:
            threshold = float(candidate.pass_threshold)
            if regression.candidate_score < threshold:
                reasons.append("candidate_below_run_pass_threshold")

        if (
            request.minimum_candidate_score is not None
            and regression.candidate_score < request.minimum_candidate_score
        ):
            reasons.append("candidate_below_minimum_score")

        return QualityGateResponse(
            decision="FAIL" if reasons else "PASS",
            reasons=reasons or ["quality_gate_passed"],
            regression=regression,
        )

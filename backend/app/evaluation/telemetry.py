from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


EVALUATION_RUNS_TOTAL = Counter(
    "redpa_evaluation_runs_total",
    "Total number of evaluation runs by terminal status.",
    ["status"],
)

EVALUATION_METRIC_SCORE = Histogram(
    "redpa_evaluation_metric_score",
    "Distribution of evaluation metric scores.",
    ["metric"],
    buckets=(0.0, 0.25, 0.5, 0.7, 0.8, 0.9, 1.0),
)

EVALUATION_AGGREGATE_SCORE = Histogram(
    "redpa_evaluation_aggregate_score",
    "Distribution of aggregate evaluation scores.",
    buckets=(0.0, 0.25, 0.5, 0.7, 0.8, 0.9, 1.0),
)

EVALUATION_METRIC_PASS_TOTAL = Counter(
    "redpa_evaluation_metric_pass_total",
    "Evaluation metric pass/fail decisions.",
    ["metric", "passed"],
)

EVALUATION_ACTIVE_RUNS = Gauge(
    "redpa_evaluation_active_runs",
    "Number of evaluation runs currently being executed.",
)

BENCHMARK_RUNS_TOTAL = Counter(
    "redpa_benchmark_runs_total",
    "Total number of benchmark runs.",
)

BENCHMARK_CASES_TOTAL = Counter(
    "redpa_benchmark_cases_total",
    "Total benchmark cases evaluated.",
    ["passed"],
)

BENCHMARK_SCORE = Histogram(
    "redpa_benchmark_score",
    "Distribution of benchmark aggregate scores.",
    buckets=(0.0, 0.25, 0.5, 0.7, 0.8, 0.9, 1.0),
)


@dataclass(slots=True)
class MetricSnapshot:
    count: int = 0
    passed: int = 0
    failed: int = 0
    score_sum: float = 0.0

    @property
    def average_score(self) -> float:
        if self.count == 0:
            return 0.0
        return self.score_sum / self.count

    def as_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "passed": self.passed,
            "failed": self.failed,
            "average_score": self.average_score,
        }


@dataclass(slots=True)
class EvaluationTelemetryState:
    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    active_runs: int = 0
    aggregate_score_sum: float = 0.0
    benchmark_runs: int = 0
    benchmark_cases: int = 0
    benchmark_passed_cases: int = 0
    metric_snapshots: dict[str, MetricSnapshot] = field(
        default_factory=lambda: defaultdict(MetricSnapshot),
    )

    @property
    def average_aggregate_score(self) -> float:
        if self.completed_runs == 0:
            return 0.0
        return self.aggregate_score_sum / self.completed_runs


class EvaluationTelemetry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = EvaluationTelemetryState()

    def run_started(self) -> None:
        with self._lock:
            self._state.total_runs += 1
            self._state.active_runs += 1
            EVALUATION_ACTIVE_RUNS.set(self._state.active_runs)

    def run_completed(self, aggregate_score: float) -> None:
        with self._lock:
            self._state.completed_runs += 1
            self._state.active_runs = max(0, self._state.active_runs - 1)
            self._state.aggregate_score_sum += aggregate_score

            EVALUATION_RUNS_TOTAL.labels(status="completed").inc()
            EVALUATION_AGGREGATE_SCORE.observe(aggregate_score)
            EVALUATION_ACTIVE_RUNS.set(self._state.active_runs)

    def run_failed(self) -> None:
        with self._lock:
            self._state.failed_runs += 1
            self._state.active_runs = max(0, self._state.active_runs - 1)

            EVALUATION_RUNS_TOTAL.labels(status="failed").inc()
            EVALUATION_ACTIVE_RUNS.set(self._state.active_runs)

    def metric_recorded(
        self,
        *,
        metric: str,
        score: float,
        passed: bool,
    ) -> None:
        with self._lock:
            snapshot = self._state.metric_snapshots[metric]
            snapshot.count += 1
            snapshot.score_sum += score

            if passed:
                snapshot.passed += 1
            else:
                snapshot.failed += 1

            EVALUATION_METRIC_SCORE.labels(metric=metric).observe(score)
            EVALUATION_METRIC_PASS_TOTAL.labels(
                metric=metric,
                passed=str(passed).lower(),
            ).inc()

    def benchmark_completed(
        self,
        *,
        aggregate_score: float,
        case_passes: list[bool],
    ) -> None:
        with self._lock:
            self._state.benchmark_runs += 1
            self._state.benchmark_cases += len(case_passes)
            self._state.benchmark_passed_cases += sum(
                1 for passed in case_passes if passed
            )

            BENCHMARK_RUNS_TOTAL.inc()
            BENCHMARK_SCORE.observe(aggregate_score)

            for passed in case_passes:
                BENCHMARK_CASES_TOTAL.labels(
                    passed=str(passed).lower(),
                ).inc()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            completed = self._state.completed_runs
            total = self._state.total_runs
            benchmark_cases = self._state.benchmark_cases

            return {
                "runs": {
                    "total": total,
                    "completed": completed,
                    "failed": self._state.failed_runs,
                    "active": self._state.active_runs,
                    "success_rate": (
                        completed / total
                        if total
                        else 0.0
                    ),
                    "average_aggregate_score": (
                        self._state.average_aggregate_score
                    ),
                },
                "metrics": {
                    name: snapshot.as_dict()
                    for name, snapshot in sorted(
                        self._state.metric_snapshots.items(),
                    )
                },
                "benchmarks": {
                    "runs": self._state.benchmark_runs,
                    "cases": benchmark_cases,
                    "passed_cases": self._state.benchmark_passed_cases,
                    "pass_rate": (
                        self._state.benchmark_passed_cases / benchmark_cases
                        if benchmark_cases
                        else 0.0
                    ),
                },
            }

    def reset_for_tests(self) -> None:
        with self._lock:
            self._state = EvaluationTelemetryState()
            EVALUATION_ACTIVE_RUNS.set(0)


evaluation_telemetry = EvaluationTelemetry()

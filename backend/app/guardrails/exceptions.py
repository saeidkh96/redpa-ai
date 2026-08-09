from __future__ import annotations

from dataclasses import dataclass

from app.guardrails.contracts import GuardrailEvaluation


@dataclass(slots=True)
class PolicyDeniedError(RuntimeError):
    evaluation: GuardrailEvaluation

    def __str__(self) -> str:
        return self.evaluation.reason


@dataclass(slots=True)
class PolicyReviewRequiredError(RuntimeError):
    evaluation: GuardrailEvaluation
    review_id: str | None = None

    def __str__(self) -> str:
        suffix = (
            f" Human review: {self.review_id}."
            if self.review_id
            else ""
        )
        return f"{self.evaluation.reason}{suffix}"

from __future__ import annotations

from app.research_workspace.schemas import (
    ResearchEvidenceItem,
    ResearchQuality,
)


class ResearchQualityEvaluator:
    @staticmethod
    def evaluate(
        evidence: list[ResearchEvidenceItem],
        *,
        target_results: int,
        minimum_score: float,
    ) -> ResearchQuality:
        count = len(evidence)
        unique_domains = len(
            {
                item.source_domain.strip().lower()
                for item in evidence
                if item.source_domain.strip()
            }
        )

        coverage = min(
            count / max(target_results, 1),
            1.0,
        )

        diversity = (
            min(unique_domains / count, 1.0)
            if count
            else 0.0
        )

        score = round(
            (coverage * 0.60)
            + (diversity * 0.40),
            4,
        )

        return ResearchQuality(
            score=score,
            coverage_score=round(coverage, 4),
            source_diversity_score=round(diversity, 4),
            evidence_count=count,
            unique_domains=unique_domains,
            passed=score >= minimum_score,
        )

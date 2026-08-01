from __future__ import annotations

from urllib.parse import urlparse

from app.schemas.research import ResearchEvidence


class ResearchConfidenceService:
    """
    Deterministically estimate confidence from evidence quality.

    This score is not a probability of truth. It is an operational
    measure of evidence coverage, quality, and diversity.
    """

    @classmethod
    def calculate(
        cls,
        *,
        evidence: list[ResearchEvidence],
        ranking_stats: dict[str, float | int],
    ) -> tuple[int, dict[str, float | int]]:
        if not evidence:
            return (
                0,
                {
                    "source_count": 0,
                    "domain_diversity": 0.0,
                    "official_source_ratio": 0.0,
                    "average_rank_score": 0.0,
                    "duplicate_ratio": 0.0,
                },
            )

        domains = {
            cls._domain(
                item.url,
            )
            for item in evidence
            if cls._domain(
                item.url,
            )
        }

        official_count = sum(
            1
            for item in evidence
            if cls._is_official(
                item,
            )
        )

        source_count_score = min(
            len(evidence)
            / 5.0,
            1.0,
        )

        domain_diversity = min(
            len(domains)
            / max(
                len(evidence),
                1,
            ),
            1.0,
        )

        official_ratio = (
            official_count
            / max(
                len(evidence),
                1,
            )
        )

        average_rank_score = float(
            ranking_stats.get(
                "average_score",
                0.0,
            )
        )

        input_count = int(
            ranking_stats.get(
                "input_count",
                len(evidence),
            )
        )

        duplicates_removed = int(
            ranking_stats.get(
                "duplicates_removed",
                0,
            )
        )

        duplicate_ratio = (
            duplicates_removed
            / max(
                input_count,
                1,
            )
        )

        confidence = (
            source_count_score * 0.25
            + domain_diversity * 0.25
            + official_ratio * 0.20
            + average_rank_score * 0.25
            + (
                1.0
                - min(
                    duplicate_ratio,
                    1.0,
                )
            )
            * 0.05
        )

        confidence_percent = round(
            max(
                0.0,
                min(
                    confidence,
                    1.0,
                ),
            )
            * 100,
        )

        return (
            confidence_percent,
            {
                "source_count": len(
                    evidence,
                ),
                "domain_diversity": round(
                    domain_diversity,
                    4,
                ),
                "official_source_ratio": round(
                    official_ratio,
                    4,
                ),
                "average_rank_score": round(
                    average_rank_score,
                    4,
                ),
                "duplicate_ratio": round(
                    duplicate_ratio,
                    4,
                ),
            },
        )

    @staticmethod
    def _domain(
        url: str,
    ) -> str:
        try:
            hostname = (
                urlparse(
                    url,
                ).hostname
                or ""
            ).casefold()
        except ValueError:
            return ""

        if hostname.startswith(
            "www.",
        ):
            hostname = hostname[4:]

        return hostname

    @classmethod
    def _is_official(
        cls,
        evidence: ResearchEvidence,
    ) -> bool:
        domain = cls._domain(
            evidence.url,
        )

        return (
            domain.endswith(
                ".gov",
            )
            or domain.endswith(
                ".edu",
            )
            or domain in {
                "docs.langchain.com",
                "langchain-ai.github.io",
                "github.com",
                "arxiv.org",
                "aclanthology.org",
                "openreview.net",
                "modelcontextprotocol.io",
            }
        )

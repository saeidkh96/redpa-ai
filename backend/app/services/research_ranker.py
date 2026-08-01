from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlparse

from app.schemas.research import ResearchEvidence


OFFICIAL_DOMAINS = {
    "docs.langchain.com",
    "langchain-ai.github.io",
    "python.langchain.com",
    "github.com",
    "arxiv.org",
    "aclanthology.org",
    "openreview.net",
    "docs.python.org",
    "fastapi.tiangolo.com",
    "modelcontextprotocol.io",
}

LOW_TRUST_DOMAIN_MARKERS = {
    "medium.com",
    "dev.to",
    "substack.com",
    "reddit.com",
    "quora.com",
    "deepwiki.com",
}


@dataclass(slots=True)
class RankedEvidence:
    evidence: ResearchEvidence
    score: float
    domain: str
    duplicate_group: str


class ResearchEvidenceRanker:
    """
    Normalize, deduplicate, and rank research evidence.

    Ranking is deterministic and independent from the LLM.
    """

    @classmethod
    def rank(
        cls,
        *,
        query: str,
        evidence: list[ResearchEvidence],
        limit: int = 6,
    ) -> tuple[
        list[ResearchEvidence],
        dict[str, float | int],
    ]:
        if not evidence:
            return (
                [],
                {
                    "input_count": 0,
                    "deduplicated_count": 0,
                    "duplicates_removed": 0,
                    "selected_count": 0,
                    "average_score": 0.0,
                },
            )

        query_terms = cls._tokenize(
            query,
        )

        ranked_candidates = [
            cls._score_item(
                evidence=item,
                query_terms=query_terms,
            )
            for item in evidence
        ]

        deduplicated = cls._deduplicate(
            ranked_candidates,
        )

        deduplicated.sort(
            key=lambda item: (
                -item.score,
                item.evidence.source_number,
            )
        )

        selected_candidates = deduplicated[
            : max(
                1,
                min(
                    int(limit),
                    10,
                ),
            )
        ]

        selected_evidence: list[
            ResearchEvidence
        ] = []

        for index, candidate in enumerate(
            selected_candidates,
            start=1,
        ):
            selected_evidence.append(
                candidate.evidence.model_copy(
                    update={
                        "source_number": index,
                        "metadata": {
                            **candidate.evidence.metadata,
                            "rank_score": round(
                                candidate.score,
                                4,
                            ),
                            "domain": candidate.domain,
                            "duplicate_group": (
                                candidate.duplicate_group
                            ),
                        },
                    }
                )
            )

        average_score = (
            sum(
                candidate.score
                for candidate in selected_candidates
            )
            / max(
                len(selected_candidates),
                1,
            )
        )

        return (
            selected_evidence,
            {
                "input_count": len(evidence),
                "deduplicated_count": len(
                    deduplicated,
                ),
                "duplicates_removed": (
                    len(evidence)
                    - len(deduplicated)
                ),
                "selected_count": len(
                    selected_evidence,
                ),
                "average_score": round(
                    average_score,
                    4,
                ),
            },
        )

    @classmethod
    def _score_item(
        cls,
        *,
        evidence: ResearchEvidence,
        query_terms: set[str],
    ) -> RankedEvidence:
        domain = cls._extract_domain(
            evidence.url,
        )

        title_terms = cls._tokenize(
            evidence.title,
        )

        snippet_terms = cls._tokenize(
            evidence.snippet,
        )

        title_overlap = cls._overlap_score(
            query_terms,
            title_terms,
        )

        snippet_overlap = cls._overlap_score(
            query_terms,
            snippet_terms,
        )

        domain_score = cls._domain_score(
            domain,
        )

        snippet_quality = cls._snippet_quality(
            evidence.snippet,
        )

        position_bonus = max(
            0.0,
            1.0
            - (
                max(
                    evidence.source_number - 1,
                    0,
                )
                * 0.05
            ),
        )

        score = (
            title_overlap * 0.35
            + snippet_overlap * 0.25
            + domain_score * 0.20
            + snippet_quality * 0.15
            + position_bonus * 0.05
        )

        duplicate_group = cls._duplicate_group(
            evidence,
            domain=domain,
        )

        return RankedEvidence(
            evidence=evidence,
            score=max(
                0.0,
                min(
                    score,
                    1.0,
                ),
            ),
            domain=domain,
            duplicate_group=duplicate_group,
        )

    @staticmethod
    def _deduplicate(
        candidates: list[RankedEvidence],
    ) -> list[RankedEvidence]:
        best_by_group: dict[
            str,
            RankedEvidence,
        ] = {}

        for candidate in candidates:
            current = best_by_group.get(
                candidate.duplicate_group,
            )

            if (
                current is None
                or candidate.score > current.score
            ):
                best_by_group[
                    candidate.duplicate_group
                ] = candidate

        return list(
            best_by_group.values(),
        )

    @staticmethod
    def _extract_domain(
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
    def _domain_score(
        cls,
        domain: str,
    ) -> float:
        if not domain:
            return 0.20

        if domain in OFFICIAL_DOMAINS:
            return 1.00

        if any(
            domain == marker
            or domain.endswith(
                "." + marker,
            )
            for marker in LOW_TRUST_DOMAIN_MARKERS
        ):
            return 0.35

        if domain.endswith(
            ".edu",
        ) or domain.endswith(
            ".gov",
        ):
            return 0.95

        if domain.endswith(
            ".org",
        ):
            return 0.75

        return 0.65

    @staticmethod
    def _snippet_quality(
        snippet: str,
    ) -> float:
        normalized = str(
            snippet or "",
        ).strip()

        length = len(
            normalized,
        )

        if length <= 20:
            return 0.10

        if length >= 300:
            return 1.00

        return min(
            1.0,
            0.20
            + (
                math.log1p(
                    length,
                )
                / math.log1p(
                    300,
                )
            )
            * 0.80,
        )

    @staticmethod
    def _overlap_score(
        query_terms: set[str],
        candidate_terms: set[str],
    ) -> float:
        if not query_terms:
            return 0.50

        if not candidate_terms:
            return 0.0

        common = (
            query_terms
            & candidate_terms
        )

        return min(
            1.0,
            len(common)
            / max(
                len(query_terms),
                1,
            ),
        )

    @classmethod
    def _duplicate_group(
        cls,
        evidence: ResearchEvidence,
        *,
        domain: str,
    ) -> str:
        title = re.sub(
            r"[^a-z0-9]+",
            " ",
            evidence.title.casefold(),
        )

        title_tokens = [
            token
            for token in title.split()
            if len(token) >= 3
        ]

        title_signature = "-".join(
            title_tokens[:8],
        )

        path = ""

        try:
            path = urlparse(
                evidence.url,
            ).path.casefold()
        except ValueError:
            pass

        path_signature = re.sub(
            r"[^a-z0-9]+",
            "-",
            path,
        ).strip("-")

        if title_signature:
            return (
                f"{domain}|{title_signature}"
            )

        return (
            f"{domain}|{path_signature}"
        )

    @staticmethod
    def _tokenize(
        value: str,
    ) -> set[str]:
        return {
            token
            for token in re.findall(
                r"[a-z0-9]{2,}",
                str(
                    value
                    or "",
                ).casefold(),
            )
            if token not in {
                "the",
                "and",
                "for",
                "with",
                "from",
                "this",
                "that",
                "what",
                "how",
                "research",
                "latest",
                "recent",
            }
        }

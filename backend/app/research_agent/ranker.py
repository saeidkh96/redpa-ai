from __future__ import annotations

import re
from urllib.parse import urlparse

from app.research_agent.schemas import ResearchEvidence


class ResearchEvidenceRanker:
    @classmethod
    def rank(
        cls,
        *,
        query: str,
        items: list[dict[str, str]],
        limit: int,
    ) -> list[ResearchEvidence]:
        query_terms = cls._tokenize(query)
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        ranked: list[ResearchEvidence] = []

        for item in items:
            title = str(item.get("title", "") or "").strip()
            url = str(item.get("href", "") or item.get("url", "") or "").strip()
            snippet = str(item.get("body", "") or item.get("snippet", "") or "").strip()

            if not title or not url:
                continue

            normalized_url = url.casefold().rstrip("/")
            normalized_title = re.sub(
                r"\s+",
                " ",
                title.casefold(),
            ).strip()

            if normalized_url in seen_urls or normalized_title in seen_titles:
                continue

            seen_urls.add(normalized_url)
            seen_titles.add(normalized_title)

            title_terms = cls._tokenize(title)
            snippet_terms = cls._tokenize(snippet)

            title_matches = query_terms & title_terms
            snippet_matches = query_terms & snippet_terms

            score = (
                len(title_matches) * 3.0
                + len(snippet_matches) * 1.0
            )

            domain = urlparse(url).netloc.casefold()

            if domain.endswith(".gov") or domain.endswith(".edu"):
                score += 0.5

            ranked.append(
                ResearchEvidence(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source_domain=domain,
                    score=round(score, 2),
                )
            )

        ranked.sort(
            key=lambda item: (
                -item.score,
                item.title.casefold(),
            )
        )

        return ranked[:limit]

    @staticmethod
    def _tokenize(
        value: str,
    ) -> set[str]:
        stop_words = {
            "a",
            "an",
            "and",
            "are",
            "for",
            "from",
            "in",
            "is",
            "of",
            "on",
            "or",
            "the",
            "to",
            "with",
        }

        return {
            token
            for token in re.findall(
                r"[a-z0-9_]{2,}",
                str(value or "").casefold(),
            )
            if token not in stop_words
        }

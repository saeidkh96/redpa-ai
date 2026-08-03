from __future__ import annotations

import asyncio
from typing import Any

from ddgs import DDGS

from app.research_agent.ranker import ResearchEvidenceRanker
from app.research_agent.schemas import ResearchResult


class ResearchAgentError(RuntimeError):
    pass


class ResearchAgentService:
    @classmethod
    async def research(
        cls,
        *,
        query: str,
        max_results: int = 8,
    ) -> ResearchResult:
        normalized_query = str(query or "").strip()

        if not normalized_query:
            raise ValueError("Research query cannot be empty.")

        raw_items = await asyncio.to_thread(
            cls._search_sync,
            normalized_query,
            max_results * 2,
        )

        evidence = ResearchEvidenceRanker.rank(
            query=normalized_query,
            items=raw_items,
            limit=max_results,
        )

        if not evidence:
            raise ResearchAgentError(
                "No usable web evidence was found."
            )

        summary = cls._build_summary(
            query=normalized_query,
            evidence=evidence,
        )

        return ResearchResult(
            query=normalized_query,
            summary=summary,
            evidence=evidence,
            total_results=len(evidence),
            provider="ddgs",
        )

    @staticmethod
    def _search_sync(
        query: str,
        max_results: int,
    ) -> list[dict[str, Any]]:
        try:
            with DDGS() as client:
                results = client.text(
                    query,
                    max_results=max_results,
                )

                return [
                    dict(item)
                    for item in results
                ]

        except Exception as exception:
            raise ResearchAgentError(
                f"Web search failed: {exception}"
            ) from exception

    @staticmethod
    def _build_summary(
        *,
        query: str,
        evidence: list,
    ) -> str:
        lines = [
            f"Research results for: {query}",
            "",
            f"Collected {len(evidence)} ranked evidence items.",
            "",
        ]

        for index, item in enumerate(
            evidence[:5],
            start=1,
        ):
            lines.extend(
                [
                    f"{index}. {item.title}",
                    f"   Source: {item.source_domain}",
                    f"   URL: {item.url}",
                    f"   Evidence: {item.snippet}",
                    "",
                ]
            )

        return "\n".join(lines).strip()

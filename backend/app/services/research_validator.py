from __future__ import annotations

import re
from collections import Counter

from app.schemas.research import ResearchEvidence


class ResearchSummaryValidator:
    """Reject corrupted, injected, or weakly grounded summaries."""

    INVALID_MARKERS = (
        "<tool_call>",
        "</tool_call>",
        "<function",
        "assistant to=",
        "system:",
        "developer:",
        "```json",
        "```xml",
    )

    @classmethod
    def is_valid(
        cls,
        *,
        summary: str,
        evidence: list[ResearchEvidence],
    ) -> bool:
        normalized = re.sub(r"\s+", " ", str(summary or "")).strip()
        if len(normalized) < 100 or len(normalized) > 3000:
            return False

        lowered = normalized.casefold()
        if any(marker in lowered for marker in cls.INVALID_MARKERS):
            return False

        if cls._non_latin_ratio(normalized) > 0.12:
            return False

        evidence_terms = cls._important_terms(
            " ".join(f"{item.title} {item.snippet}" for item in evidence)
        )
        summary_terms = cls._important_terms(normalized)
        if not evidence_terms or not summary_terms:
            return False

        grounded_terms = summary_terms & evidence_terms
        grounding_ratio = len(grounded_terms) / max(len(summary_terms), 1)
        return grounding_ratio >= 0.45

    @staticmethod
    def _non_latin_ratio(value: str) -> float:
        letters = [character for character in value if character.isalpha()]
        if not letters:
            return 0.0
        non_latin = sum(
            1
            for character in letters
            if not (
                "LATIN" in __import__("unicodedata").name(character, "")
            )
        )
        return non_latin / len(letters)

    @staticmethod
    def _important_terms(value: str) -> set[str]:
        stopwords = {
            "the", "and", "for", "with", "that", "this", "from", "into",
            "are", "was", "were", "has", "have", "had", "can", "could",
            "would", "should", "about", "through", "using", "used", "use",
            "their", "they", "them", "which", "when", "where", "what",
            "research", "evidence", "source", "sources",
        }
        terms = re.findall(r"[a-z0-9][a-z0-9_-]{2,}", value.casefold())
        counts = Counter(term for term in terms if term not in stopwords)
        return {term for term, count in counts.items() if count >= 1}

from __future__ import annotations

import re

from app.schemas.research import ResearchEvidence


class ResearchResponseFormatter:
    """
    Build the final Markdown response without delegating citations or
    source formatting to the language model.
    """

    @classmethod
    def format(
        cls,
        *,
        query: str,
        summary: str,
        evidence: list[ResearchEvidence],
        confidence: int,
    ) -> str:
        cleaned_summary = cls._clean_summary(
            summary,
        )

        findings = cls._build_findings(
            evidence,
        )

        lines = [
            "## Summary",
            "",
            cleaned_summary,
            "",
            "## Key Findings",
            "",
        ]

        if findings:
            lines.extend(
                findings,
            )
        else:
            lines.append(
                "- No reliable key findings were extracted."
            )

        lines.extend(
            [
                "",
                "## Confidence",
                "",
                f"**{confidence}%**",
                "",
                (
                    "This confidence score reflects evidence "
                    "coverage, source diversity, source quality, "
                    "and duplicate removal. It is not a guarantee "
                    "that every claim is correct."
                ),
                "",
                "## Sources",
                "",
            ]
        )

        for item in evidence:
            domain = str(
                item.metadata.get(
                    "domain",
                    "",
                )
                or ""
            ).strip()

            domain_suffix = (
                f" ({domain})"
                if domain
                else ""
            )

            lines.append(
                f"[{item.source_number}] "
                f"{item.title}{domain_suffix}"
            )

            lines.append(
                item.url,
            )

            lines.append("")

        lines.extend(
            [
                "## Limitations",
                "",
                (
                    "- The research is based on search-result "
                    "titles and snippets; full pages were not "
                    "retrieved in this phase."
                ),
                (
                    "- The confidence score measures evidence "
                    "quality and diversity, not absolute truth."
                ),
                (
                    "- Important sources may be absent from the "
                    "search results."
                ),
            ]
        )

        return "\n".join(
            lines,
        ).strip()

    @staticmethod
    def _build_findings(
        evidence: list[ResearchEvidence],
    ) -> list[str]:
        findings: list[str] = []

        for item in evidence[
            :5
        ]:
            snippet = re.sub(
                r"\s+",
                " ",
                item.snippet.strip(),
            )

            if not snippet:
                continue

            if len(snippet) > 320:
                snippet = (
                    snippet[:317].rstrip()
                    + "..."
                )

            findings.append(
                f"- {snippet} "
                f"[{item.source_number}]"
            )

        return findings

    @staticmethod
    def _clean_summary(
        summary: str,
    ) -> str:
        cleaned = str(
            summary
            or "",
        ).strip()

        cleaned = re.sub(
            r"<\s*/?\s*(tool_call|function|assistant|system)"
            r"[^>]*>",
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()

        if len(cleaned) > 3000:
            cleaned = (
                cleaned[:2997].rstrip()
                + "..."
            )

        if len(cleaned) < 40:
            return (
                "The available evidence was collected and ranked, "
                "but the local language model did not return a "
                "sufficiently reliable synthesis. Review the key "
                "findings and sources below."
            )

        return cleaned

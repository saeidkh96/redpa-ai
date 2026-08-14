from __future__ import annotations

from app.research_workspace.schemas import (
    ResearchEvidenceItem,
    ResearchQuality,
)


class EnterpriseResearchReportBuilder:
    @staticmethod
    def build(
        *,
        query: str,
        evidence: list[ResearchEvidenceItem],
        quality: ResearchQuality,
    ) -> str:
        lines = [
            f"# Enterprise Research Report",
            "",
            f"## Research Question",
            "",
            query,
            "",
            "## Executive Evidence Summary",
            "",
            (
                f"RedPA collected {len(evidence)} ranked evidence items "
                f"from {quality.unique_domains} unique source domains. "
                f"The deterministic research-quality score is "
                f"{quality.score:.3f}."
            ),
            "",
            "## Evidence",
            "",
        ]

        for index, item in enumerate(evidence, start=1):
            lines.extend(
                [
                    f"### {index}. {item.title}",
                    "",
                    f"- Source: {item.source_domain}",
                    f"- URL: {item.url}",
                    f"- Retrieval score: {item.score:.3f}",
                    f"- Evidence: {item.snippet}",
                    "",
                ]
            )

        lines.extend(
            [
                "## Quality",
                "",
                f"- Coverage: {quality.coverage_score:.3f}",
                f"- Source diversity: {quality.source_diversity_score:.3f}",
                f"- Overall score: {quality.score:.3f}",
                f"- Gate: {'PASS' if quality.passed else 'REVIEW'}",
                "",
                "## Provenance",
                "",
                (
                    "This report is evidence-first: the source URLs and snippets "
                    "above are the retrieved research evidence used by the V7 "
                    "Enterprise Research Workspace. RedPA does not claim that a "
                    "retrieved snippet independently proves claims outside its "
                    "displayed context."
                ),
            ]
        )

        return "\n".join(lines).strip()

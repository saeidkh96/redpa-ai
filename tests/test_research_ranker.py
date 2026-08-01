from app.schemas.research import ResearchEvidence
from app.services.research_ranker import (
    ResearchEvidenceRanker,
)


def test_ranker_removes_duplicate_titles() -> None:
    evidence = [
        ResearchEvidence(
            source_number=1,
            title="LangGraph Durable Execution",
            url="https://docs.langchain.com/a",
            snippet="LangGraph persists workflow state.",
            provider="ddgs",
            metadata={},
        ),
        ResearchEvidence(
            source_number=2,
            title="LangGraph Durable Execution",
            url="https://docs.langchain.com/b",
            snippet="Duplicate result.",
            provider="ddgs",
            metadata={},
        ),
    ]

    ranked, stats = ResearchEvidenceRanker.rank(
        query="LangGraph durable execution",
        evidence=evidence,
        limit=6,
    )

    assert len(ranked) == 1
    assert stats["duplicates_removed"] == 1

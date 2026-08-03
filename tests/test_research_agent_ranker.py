from app.research_agent.ranker import (
    ResearchEvidenceRanker,
)


def test_ranker_prefers_query_matches() -> None:
    result = ResearchEvidenceRanker.rank(
        query="LangGraph durable execution",
        items=[
            {
                "title": "General AI News",
                "href": "https://example.com/general",
                "body": "General artificial intelligence news.",
            },
            {
                "title": "LangGraph Durable Execution",
                "href": "https://example.com/langgraph",
                "body": "LangGraph workflows and durable execution.",
            },
        ],
        limit=5,
    )

    assert result[0].title == (
        "LangGraph Durable Execution"
    )
    assert result[0].score > result[1].score


def test_ranker_removes_duplicates() -> None:
    result = ResearchEvidenceRanker.rank(
        query="agentic AI",
        items=[
            {
                "title": "Agentic AI",
                "href": "https://example.com/a",
                "body": "Agentic AI systems.",
            },
            {
                "title": "Agentic AI",
                "href": "https://example.com/a",
                "body": "Duplicate.",
            },
        ],
        limit=5,
    )

    assert len(result) == 1

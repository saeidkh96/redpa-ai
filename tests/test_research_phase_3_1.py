from app.agents.router import SUPPORTED_ROUTE_DESTINATIONS
from app.agents.state import AgentState


def test_research_route_is_enabled() -> None:
    assert (
        SUPPORTED_ROUTE_DESTINATIONS["research"]
        == "research"
    )


def test_research_state_accepts_fields() -> None:
    state: AgentState = {
        "research_query": "LangGraph durable execution",
        "research_evidence": [],
        "research_sources": [],
        "research_summary": None,
        "research_provider": None,
        "research_error": None,
        "research_execution_time_ms": 0.0,
    }

    assert state["research_query"] is not None

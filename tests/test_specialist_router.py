from app.a2a_protocol.specialist_router import CoordinatorSpecialistRouter


def test_selects_research_agent() -> None:
    result = CoordinatorSpecialistRouter.select("Research recent agentic AI evidence.")
    assert result is not None
    assert result.name == "research-agent"


def test_selects_docker_agent() -> None:
    result = CoordinatorSpecialistRouter.select("Show Docker containers.")
    assert result is not None
    assert result.name == "docker-agent"


def test_returns_none_for_unknown_request() -> None:
    assert CoordinatorSpecialistRouter.select("Hello there.") is None

from dataclasses import dataclass, field

from app.a2a_remote.registry import RemoteAgentRecord
from app.services.a2a_chat_service import A2AChatService


@dataclass
class FakeSkill:
    id: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


@dataclass
class FakeCard:
    name: str
    description: str
    skills: list[FakeSkill]


def make_record(
    *,
    name: str,
    skill: FakeSkill,
) -> RemoteAgentRecord:
    return RemoteAgentRecord(
        name=name,
        base_url=f"http://{name}:8050",
        enabled=True,
        timeout_seconds=30,
        card=FakeCard(
            name=name,
            description="Remote agent.",
            skills=[skill],
        ),
        connected=True,
    )


def test_selects_docker_skill() -> None:
    research = make_record(
        name="research-agent",
        skill=FakeSkill(
            id="web_research",
            name="Web Research",
            description="Research web evidence.",
            tags=["research", "web", "sources"],
        ),
    )

    docker = make_record(
        name="docker-agent",
        skill=FakeSkill(
            id="docker_inspection",
            name="Docker Inspection",
            description="Inspect containers and logs.",
            tags=["docker", "containers", "logs"],
        ),
    )

    selected, metadata = (
        A2AChatService.select_remote_agent(
            user_message=(
                "Which agent can inspect Docker containers and logs?"
            ),
            records=[research, docker],
        )
    )

    assert selected.name == "docker-agent"
    assert metadata["selected_skill"] == "docker_inspection"
    assert metadata["score"] > 0


def test_selects_research_skill() -> None:
    research = make_record(
        name="research-agent",
        skill=FakeSkill(
            id="web_research",
            name="Web Research",
            description="Research current web evidence.",
            tags=["research", "web", "evidence"],
        ),
    )

    docker = make_record(
        name="docker-agent",
        skill=FakeSkill(
            id="docker_inspection",
            name="Docker Inspection",
            description="Inspect Docker containers.",
            tags=["docker", "containers"],
        ),
    )

    selected, _ = A2AChatService.select_remote_agent(
        user_message=(
            "Find an agent for current web research and evidence."
        ),
        records=[docker, research],
    )

    assert selected.name == "research-agent"

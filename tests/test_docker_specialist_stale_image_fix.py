from pathlib import Path


def test_container_listing_does_not_use_container_image() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "backend"
        / "app"
        / "specialist_agents"
        / "docker_agent.py"
    ).read_text(
        encoding="utf-8",
    )

    assert "container.image.tags" not in source
    assert (
        'container.attrs.get(\n'
        '                            "Config",'
    ) in source

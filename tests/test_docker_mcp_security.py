import pytest

from app.mcp_servers.docker_security import (
    DockerMCPValidationError,
    normalize_log_tail,
    validate_container_reference,
)


def test_accepts_safe_container_reference() -> None:
    assert validate_container_reference(
        "redpa-backend"
    ) == "redpa-backend"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "../container",
        "/var/run/docker.sock",
        "container name",
        "name;rm",
    ],
)
def test_rejects_unsafe_container_reference(
    value: str,
) -> None:
    with pytest.raises(
        DockerMCPValidationError,
    ):
        validate_container_reference(
            value,
        )


def test_caps_log_tail() -> None:
    assert normalize_log_tail(
        5_000,
    ) == 2_000

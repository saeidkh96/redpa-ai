from app.specialist_agents.docker_agent import (
    INSPECT_PATTERNS,
    LIST_CONTAINER_PATTERNS,
    LIST_IMAGE_PATTERNS,
    LOG_PATTERNS,
    _extract_with_patterns,
    _matches_any,
)


def test_show_docker_containers_is_list_intent() -> None:
    assert _matches_any(
        "show Docker containers",
        LIST_CONTAINER_PATTERNS,
    )


def test_docker_ps_is_list_intent() -> None:
    assert _matches_any(
        "docker ps",
        LIST_CONTAINER_PATTERNS,
    )


def test_list_images_is_image_intent() -> None:
    assert _matches_any(
        "list Docker images",
        LIST_IMAGE_PATTERNS,
    )


def test_extracts_inspect_target() -> None:
    assert (
        _extract_with_patterns(
            "inspect container redpa-backend",
            INSPECT_PATTERNS,
        )
        == "redpa-backend"
    )


def test_extracts_log_target() -> None:
    assert (
        _extract_with_patterns(
            "show logs for redpa-backend",
            LOG_PATTERNS,
        )
        == "redpa-backend"
    )


def test_list_request_is_not_inspect_target() -> None:
    assert (
        _extract_with_patterns(
            "show Docker containers",
            INSPECT_PATTERNS,
        )
        is None
    )

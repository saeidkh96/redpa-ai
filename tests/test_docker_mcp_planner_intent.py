from app.mcp.planner_intent import (
    detect_mcp_tool_intent,
)


def test_list_containers_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Show Docker containers"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-docker:list_containers"
    )


def test_running_containers_intent() -> None:
    intent = detect_mcp_tool_intent(
        "List running Docker containers"
    )

    assert intent is not None
    assert intent.arguments["all_containers"] is False


def test_container_logs_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Show last 50 logs for redpa-backend"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-docker:container_logs"
    )
    assert intent.arguments["container"] == (
        "redpa-backend"
    )
    assert intent.arguments["tail"] == 50


def test_list_images_intent() -> None:
    intent = detect_mcp_tool_intent(
        "List Docker images"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-docker:list_images"
    )


def test_system_info_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Show Docker system info"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-docker:system_info"
    )

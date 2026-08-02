import pytest

from app.mcp_servers.github_client import (
    GitHubAPIClient,
)


def test_repository_parser_accepts_owner_name() -> None:
    assert GitHubAPIClient.parse_repository(
        "langchain-ai/langgraph"
    ) == (
        "langchain-ai",
        "langgraph",
    )


def test_repository_parser_accepts_github_url() -> None:
    assert GitHubAPIClient.parse_repository(
        "https://github.com/openai/openai-python"
    ) == (
        "openai",
        "openai-python",
    )


def test_repository_parser_rejects_invalid_value() -> None:
    with pytest.raises(
        ValueError,
    ):
        GitHubAPIClient.parse_repository(
            "../../etc/passwd"
        )

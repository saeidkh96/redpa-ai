import pytest

from app.a2a_remote.client import (
    RemoteA2AClient,
)


def test_accepts_http_remote_url() -> None:
    assert RemoteA2AClient.validate_base_url(
        "http://a2a-coordinator:8050/"
    ) == "http://a2a-coordinator:8050"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "file:///tmp/agent",
        "ftp://example.com",
        "http://user:pass@example.com",
    ],
)
def test_rejects_invalid_remote_url(
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        RemoteA2AClient.validate_base_url(
            value,
        )

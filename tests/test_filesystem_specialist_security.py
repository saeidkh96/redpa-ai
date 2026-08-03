import pytest
from app.specialist_agents.filesystem_agent import _resolve_safe_path


def test_accepts_backend_path() -> None:
    assert _resolve_safe_path("backend/app").name == "app"


@pytest.mark.parametrize("path", ["../.env", "/etc/passwd", ".env"])
def test_rejects_unsafe_path(path: str) -> None:
    with pytest.raises(ValueError):
        _resolve_safe_path(path)

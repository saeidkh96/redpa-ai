from pathlib import Path

import pytest

from app.mcp_servers.filesystem_security import (
    FilesystemAccessError,
    ReadOnlyFilesystemSandbox,
)


def test_sandbox_rejects_parent_traversal(
    tmp_path: Path,
) -> None:
    backend = tmp_path / "backend"
    docs = tmp_path / "docs"
    backend.mkdir()
    docs.mkdir()
    (tmp_path / "README.md").write_text(
        "hello",
        encoding="utf-8",
    )

    sandbox = ReadOnlyFilesystemSandbox(
        tmp_path,
    )

    with pytest.raises(
        FilesystemAccessError,
    ):
        sandbox.resolve(
            "backend/../../secret.txt",
            must_exist=False,
        )


def test_sandbox_accepts_backend_file(
    tmp_path: Path,
) -> None:
    backend = tmp_path / "backend"
    docs = tmp_path / "docs"
    backend.mkdir()
    docs.mkdir()

    file_path = backend / "main.py"
    file_path.write_text(
        "print('ok')",
        encoding="utf-8",
    )

    (tmp_path / "README.md").write_text(
        "hello",
        encoding="utf-8",
    )

    sandbox = ReadOnlyFilesystemSandbox(
        tmp_path,
    )

    resolved = sandbox.resolve(
        "backend/main.py",
    )

    assert resolved == file_path.resolve()
    assert sandbox.to_public_path(
        resolved,
    ) == "backend/main.py"


def test_sandbox_blocks_env_files(
    tmp_path: Path,
) -> None:
    backend = tmp_path / "backend"
    docs = tmp_path / "docs"
    backend.mkdir()
    docs.mkdir()

    env_file = backend / ".env"
    env_file.write_text(
        "SECRET=value",
        encoding="utf-8",
    )

    (tmp_path / "README.md").write_text(
        "hello",
        encoding="utf-8",
    )

    sandbox = ReadOnlyFilesystemSandbox(
        tmp_path,
    )

    with pytest.raises(
        FilesystemAccessError,
    ):
        sandbox.resolve(
            "backend/.env",
        )

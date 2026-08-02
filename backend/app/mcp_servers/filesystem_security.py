from __future__ import annotations

import os
from pathlib import Path


class FilesystemAccessError(ValueError):
    """Raised when a requested path is outside the read-only sandbox."""


class ReadOnlyFilesystemSandbox:
    """
    Resolve user-facing paths inside a fixed read-only workspace.

    Exposed paths:
    - backend/
    - docs/
    - README.md
    """

    BLOCKED_NAMES = {
        ".env",
        ".env.local",
        ".env.production",
        ".git",
        ".idea",
        ".vscode",
        "__pycache__",
        "node_modules",
    }

    BLOCKED_SUFFIXES = {
        ".key",
        ".pem",
        ".p12",
        ".pfx",
        ".crt",
        ".cer",
        ".sqlite",
        ".sqlite3",
        ".db",
        ".pyc",
        ".pyo",
    }

    TEXT_SUFFIXES = {
        ".c",
        ".cc",
        ".cpp",
        ".css",
        ".csv",
        ".dockerfile",
        ".go",
        ".h",
        ".hpp",
        ".html",
        ".ini",
        ".java",
        ".js",
        ".json",
        ".jsx",
        ".md",
        ".mjs",
        ".properties",
        ".py",
        ".rst",
        ".sh",
        ".sql",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }

    def __init__(
        self,
        workspace_root: str | Path,
    ) -> None:
        self.workspace_root = Path(
            workspace_root,
        ).resolve()

        self.allowed_roots = {
            "backend": (
                self.workspace_root
                / "backend"
            ).resolve(),
            "docs": (
                self.workspace_root
                / "docs"
            ).resolve(),
        }

        self.allowed_files = {
            "README.md": (
                self.workspace_root
                / "README.md"
            ).resolve(),
        }

    def resolve(
        self,
        requested_path: str,
        *,
        must_exist: bool = True,
    ) -> Path:
        normalized = self._normalize_user_path(
            requested_path,
        )

        if normalized in {
            "",
            ".",
        }:
            return self.workspace_root

        if normalized in self.allowed_files:
            candidate = self.allowed_files[
                normalized
            ]
            self._validate_candidate(
                candidate,
            )
            return candidate

        first_component, _, remainder = (
            normalized.partition(
                "/",
            )
        )

        root = self.allowed_roots.get(
            first_component,
        )

        if root is None:
            raise FilesystemAccessError(
                "Path must be inside backend/, docs/, or README.md."
            )

        candidate = (
            root
            / remainder
        ).resolve()

        if not self._is_relative_to(
            candidate,
            root,
        ):
            raise FilesystemAccessError(
                "Path traversal outside the sandbox is not allowed."
            )

        self._validate_candidate(
            candidate,
        )

        if must_exist and not candidate.exists():
            raise FilesystemAccessError(
                f"Path does not exist: {normalized}"
            )

        return candidate

    def to_public_path(
        self,
        path: Path,
    ) -> str:
        resolved = path.resolve()

        if resolved in self.allowed_files.values():
            return "README.md"

        for name, root in self.allowed_roots.items():
            if self._is_relative_to(
                resolved,
                root,
            ):
                relative = resolved.relative_to(
                    root,
                )

                if str(relative) == ".":
                    return name

                return (
                    f"{name}/"
                    f"{relative.as_posix()}"
                )

        raise FilesystemAccessError(
            "Resolved path is outside the public sandbox."
        )

    def is_text_file(
        self,
        path: Path,
    ) -> bool:
        if path.name == "README.md":
            return True

        suffix = path.suffix.casefold()

        if suffix in self.TEXT_SUFFIXES:
            return True

        if not suffix and path.name.casefold() in {
            "dockerfile",
            "makefile",
            "license",
        }:
            return True

        return False

    def should_hide(
        self,
        path: Path,
    ) -> bool:
        name = path.name.casefold()

        if name in {
            value.casefold()
            for value in self.BLOCKED_NAMES
        }:
            return True

        if path.suffix.casefold() in self.BLOCKED_SUFFIXES:
            return True

        if name.startswith(
            ".env",
        ):
            return True

        return False

    @staticmethod
    def _normalize_user_path(
        value: str,
    ) -> str:
        normalized = str(
            value
            or ""
        ).strip()

        normalized = normalized.replace(
            "\\",
            "/",
        )

        while normalized.startswith(
            "./",
        ):
            normalized = normalized[2:]

        if "\x00" in normalized:
            raise FilesystemAccessError(
                "NUL bytes are not allowed in paths."
            )

        if normalized.startswith(
            "/",
        ):
            raise FilesystemAccessError(
                "Absolute paths are not allowed."
            )

        if len(normalized) >= 2 and normalized[1] == ":":
            raise FilesystemAccessError(
                "Windows absolute paths are not allowed."
            )

        return normalized.rstrip(
            "/",
        )

    def _validate_candidate(
        self,
        path: Path,
    ) -> None:
        for component in path.parts:
            component_name = component.casefold()

            if component_name in {
                value.casefold()
                for value in self.BLOCKED_NAMES
            }:
                raise FilesystemAccessError(
                    f"Access to '{component}' is blocked."
                )

        if self.should_hide(
            path,
        ):
            raise FilesystemAccessError(
                f"Access to '{path.name}' is blocked."
            )

        if path.is_symlink():
            raise FilesystemAccessError(
                "Symbolic links are not exposed."
            )

    @staticmethod
    def _is_relative_to(
        path: Path,
        root: Path,
    ) -> bool:
        try:
            path.relative_to(
                root,
            )
            return True
        except ValueError:
            return False


def get_workspace_root() -> Path:
    return Path(
        os.getenv(
            "FILESYSTEM_MCP_ROOT",
            "/workspace",
        )
    )

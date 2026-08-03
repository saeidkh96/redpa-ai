from __future__ import annotations

from pathlib import Path
from zipfile import (
    ZIP_DEFLATED,
    ZipFile,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist" / "redpa-ai-v1.0.0.zip"


EXCLUDED_PARTS = {
    ".git",
    ".github",
    ".idea",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
}


EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
}


def should_include(
    path: Path,
) -> bool:
    relative = path.relative_to(ROOT)

    if any(
        part in EXCLUDED_PARTS
        for part in relative.parts
    ):
        return False

    if path.suffix.casefold() in EXCLUDED_SUFFIXES:
        return False

    if path.name in {
        ".env",
        "release-check-report.json",
    }:
        return False

    return True


def main() -> None:
    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if OUTPUT.exists():
        OUTPUT.unlink()

    with ZipFile(
        OUTPUT,
        "w",
        ZIP_DEFLATED,
    ) as archive:
        for path in ROOT.rglob("*"):
            if (
                path.is_file()
                and should_include(path)
            ):
                archive.write(
                    path,
                    path.relative_to(ROOT),
                )

    print(
        f"Release archive created: {OUTPUT}"
    )


if __name__ == "__main__":
    main()

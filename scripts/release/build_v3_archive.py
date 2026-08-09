from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"
ARCHIVE = DIST / "redpa-ai-v3.0.0.zip"
SHA_FILE = DIST / "redpa-ai-v3.0.0.sha256"

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "uploads",
}

EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
}


def include(path: Path) -> bool:
    relative = path.relative_to(ROOT)

    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False

    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False

    if path.name in {".env"}:
        return False

    return True


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)

    if ARCHIVE.exists():
        ARCHIVE.unlink()

    with zipfile.ZipFile(
        ARCHIVE,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file() and include(path):
                archive.write(
                    path,
                    path.relative_to(ROOT),
                )

    digest = hashlib.sha256(
        ARCHIVE.read_bytes()
    ).hexdigest().upper()

    SHA_FILE.write_text(
        f"{digest}  {ARCHIVE.name}\n",
        encoding="utf-8",
    )

    print(ARCHIVE)
    print(SHA_FILE)
    print(digest)


if __name__ == "__main__":
    main()

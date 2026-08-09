import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_manifest_is_v3() -> None:
    payload = json.loads(
        (
            ROOT / "RELEASE_MANIFEST_v3.0.0.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["version"] == "3.0.0"


def test_v3_release_docs_exist() -> None:
    for path in (
        "docs/release/V3_RELEASE_NOTES.md",
        "docs/release/V3_CAPABILITY_MATRIX.md",
        "docs/release/V3_PORTFOLIO_SUMMARY.md",
        "docs/release/V3_FINAL_CHECKLIST.md",
    ):
        assert (ROOT / path).is_file(), path


def test_release_builder_exists() -> None:
    assert (
        ROOT / "scripts/release/build_v3_archive.py"
    ).is_file()

from pathlib import Path

from app.architecture.boundaries import CONTEXTS, context_names


ROOT = Path(__file__).resolve().parents[1]


def test_bounded_context_names_are_unique() -> None:
    names = context_names()
    assert len(names) == len(set(names))
    assert len(names) >= 7


def test_every_bounded_context_has_responsibility() -> None:
    assert all(context.responsibility.strip() for context in CONTEXTS)


def test_architecture_docs_exist() -> None:
    required = (
        "docs/architecture/ddd.md",
        "docs/architecture/clean-architecture.md",
        "docs/architecture/c4.md",
        "docs/architecture/arc42.md",
    )
    for relative in required:
        assert (ROOT / relative).is_file(), relative


def test_minimum_adr_set_exists() -> None:
    adr_dir = ROOT / "docs" / "architecture" / "adr"
    adrs = sorted(adr_dir.glob("*.md"))
    assert len(adrs) >= 5


def test_domain_contract_modules_do_not_import_fastapi() -> None:
    candidates = [
        ROOT / "backend" / "app" / "guardrails" / "contracts.py",
        ROOT / "backend" / "app" / "model_gateway" / "contracts.py",
        ROOT / "backend" / "app" / "architecture" / "boundaries.py",
    ]
    for path in candidates:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            assert "fastapi" not in content.lower(), str(path)


def test_domain_contract_modules_do_not_import_sqlalchemy() -> None:
    candidates = [
        ROOT / "backend" / "app" / "guardrails" / "contracts.py",
        ROOT / "backend" / "app" / "model_gateway" / "contracts.py",
        ROOT / "backend" / "app" / "architecture" / "boundaries.py",
    ]
    for path in candidates:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            assert "sqlalchemy" not in content.lower(), str(path)

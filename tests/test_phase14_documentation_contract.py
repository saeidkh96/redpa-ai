from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_c4_has_required_levels() -> None:
    content = _read("docs/architecture/c4.md")
    assert "Level 1" in content
    assert "Level 2" in content
    assert "Level 3" in content


def test_arc42_has_core_sections() -> None:
    content = _read("docs/architecture/arc42.md")
    for section in (
        "Introduction and Goals",
        "Constraints",
        "Context and Scope",
        "Solution Strategy",
        "Building Block View",
        "Runtime View",
        "Deployment View",
        "Cross-Cutting Concepts",
        "Architecture Decisions",
        "Quality Requirements",
        "Risks and Technical Debt",
        "Glossary",
    ):
        assert section in content


def test_ddd_names_core_contexts() -> None:
    content = _read("docs/architecture/ddd.md")
    for context in (
        "Agent Orchestration",
        "Knowledge & Retrieval",
        "Human Oversight",
        "Tooling & Integration",
        "Model Runtime",
        "Policy & Governance",
        "Platform Operations",
    ):
        assert context in content

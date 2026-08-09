from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[1]
AZURE = ROOT / "infra" / "azure"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_pulumi_project_exists() -> None:
    assert (AZURE / "Pulumi.yaml").is_file()
    assert (AZURE / "__main__.py").is_file()
    assert (AZURE / "requirements.txt").is_file()


def test_cloud_docs_exist() -> None:
    for relative in (
        "docs/cloud/azure-architecture.md",
        "docs/cloud/security.md",
        "docs/cloud/cost.md",
        "docs/cloud/runbook.md",
    ):
        assert (ROOT / relative).is_file(), relative


def test_naming_is_deterministic() -> None:
    naming = _load_module(
        "phase15_naming",
        AZURE / "naming.py",
    )

    assert (
        naming.resource_name(
            "RedPA AI",
            "DEV",
            "Backend",
        )
        == "redpa-ai-dev-backend"
    )

    assert naming.acr_name(
        "RedPA-AI",
        "DEV",
    ).isalnum()


def test_naming_respects_length_limit() -> None:
    naming = _load_module(
        "phase15_naming_limit",
        AZURE / "naming.py",
    )
    name = naming.resource_name(
        "redpa" * 30,
        "production",
        "backend",
        max_length=63,
    )
    assert len(name) <= 63


def test_standard_tags_cover_governance() -> None:
    tags = _load_module(
        "phase15_tags",
        AZURE / "tags.py",
    )
    result = tags.standard_tags(
        project="redpa",
        environment="dev",
    )

    assert result["managed-by"] == "pulumi"
    assert result["platform"] == "redpa-ai"
    assert result["architecture-phase"] == "15"

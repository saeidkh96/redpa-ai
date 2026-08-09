from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AZURE = ROOT / "infra" / "azure"


def _read(name: str) -> str:
    return (AZURE / name).read_text(encoding="utf-8")


def test_foundation_contains_expected_azure_services() -> None:
    content = _read("foundation.py")

    assert "ResourceGroup" in content
    assert "Registry" in content
    assert "Vault" in content
    assert "Workspace" in content


def test_database_uses_postgresql_flexible_server() -> None:
    content = _read("database.py")

    assert "dbforpostgresql.Server" in content
    assert "dbforpostgresql.Database" in content
    assert "Standard_B1ms" in content


def test_container_apps_include_three_redpa_workloads() -> None:
    content = _read("container_apps.py")

    assert '"policy-service"' in content
    assert '"backend"' in content
    assert '"frontend"' in content
    assert "ManagedEnvironment" in content
    assert "ContainerApp" in content


def test_acr_admin_user_is_disabled() -> None:
    content = _read("foundation.py")

    assert "admin_user_enabled=False" in content


def test_secret_values_are_not_hardcoded_in_example_config() -> None:
    content = _read("Pulumi.dev.yaml.example")

    assert "postgresPassword:" not in content
    assert "pulumi config set --secret" in content

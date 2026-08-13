from pathlib import Path
import json


def test_v6_release_version_contract():
    config_source = Path("backend/app/core/config.py").read_text(encoding="utf-8")
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    frontend = json.loads(Path("frontend/package.json").read_text(encoding="utf-8"))
    sdk = Path("sdk/python/pyproject.toml").read_text(encoding="utf-8")

    assert 'default="6.0.0"' in config_source
    assert 'APP_VERSION: "6.0.0"' in compose
    assert frontend["version"] == "6.0.0"
    assert 'version = "6.0.0"' in sdk


def test_compose_release_version_is_not_overridden_by_host_app_version():
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert "${APP_VERSION" not in compose

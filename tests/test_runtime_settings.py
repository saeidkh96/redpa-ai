from app.core.runtime_settings import (
    RuntimeSettings,
)


def test_runtime_settings_defaults(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "ENVIRONMENT",
        raising=False,
    )

    settings = RuntimeSettings.load()

    assert settings.environment == "development"
    assert settings.json_logs is True

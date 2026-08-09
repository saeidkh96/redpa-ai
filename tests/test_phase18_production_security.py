import pytest

from app.security.production_guard import (
    assert_production_configuration,
    evaluate_production_configuration,
)


def good_prod_env() -> dict[str, str]:
    return {
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "EXPOSE_ERROR_DETAILS": "false",
        "REQUIRE_HTTPS": "true",
        "JWT_SECRET_KEY": "x" * 64,
        "ALLOWED_HOSTS": "api.example.com",
        "CORS_ORIGINS": "https://app.example.com",
    }


def test_secure_production_configuration_passes() -> None:
    assert evaluate_production_configuration(
        good_prod_env()
    ) == ()


def test_debug_is_rejected_in_production() -> None:
    env = good_prod_env()
    env["DEBUG"] = "true"

    findings = evaluate_production_configuration(env)
    assert any(
        item.code == "PROD_DEBUG_ENABLED"
        for item in findings
    )


def test_weak_secret_is_rejected() -> None:
    env = good_prod_env()
    env["JWT_SECRET_KEY"] = "weak"

    with pytest.raises(RuntimeError):
        assert_production_configuration(env)


def test_wildcard_cors_is_rejected() -> None:
    env = good_prod_env()
    env["CORS_ORIGINS"] = "*"

    findings = evaluate_production_configuration(env)
    assert any(
        item.code == "PROD_WILDCARD_CORS"
        for item in findings
    )

from app.security_hardening.api_keys import (
    APIKeyService,
)


def test_api_key_hash_and_verify(monkeypatch):
    monkeypatch.setenv(
        "API_KEY_PEPPER",
        "test-pepper",
    )

    generated = APIKeyService.generate()

    assert APIKeyService.verify(
        generated.raw_key,
        generated.key_hash,
    )

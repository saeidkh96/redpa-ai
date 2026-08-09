from app.auth.oauth import (
    OAuthProviderConfig,
    build_authorization_request,
    build_pkce_challenge,
)


def test_pkce_challenge_is_url_safe() -> None:
    challenge = build_pkce_challenge("a" * 64)
    assert "=" not in challenge
    assert challenge


def test_authorization_request_contains_pkce_and_state() -> None:
    request = build_authorization_request(
        config=OAuthProviderConfig(
            provider="test",
            client_id="client",
            authorization_endpoint="https://example.com/oauth/authorize",
            token_endpoint="https://example.com/oauth/token",
            userinfo_endpoint=None,
            scopes=("openid", "email"),
        ),
        redirect_uri="http://localhost/callback",
    )

    assert "code_challenge_method=S256" in request.url
    assert "state=" in request.url
    assert request.state
    assert request.code_verifier

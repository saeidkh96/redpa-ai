from __future__ import annotations

import os

from app.auth.oauth import OAuthProviderConfig


def github_provider() -> OAuthProviderConfig | None:
    client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID", "").strip()
    if not client_id:
        return None

    return OAuthProviderConfig(
        provider="github",
        client_id=client_id,
        authorization_endpoint="https://github.com/login/oauth/authorize",
        token_endpoint="https://github.com/login/oauth/access_token",
        userinfo_endpoint="https://api.github.com/user",
        scopes=("read:user", "user:email"),
    )


def google_provider() -> OAuthProviderConfig | None:
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    if not client_id:
        return None

    return OAuthProviderConfig(
        provider="google",
        client_id=client_id,
        authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint="https://oauth2.googleapis.com/token",
        userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
        scopes=("openid", "email", "profile"),
    )


def enabled_oauth_providers() -> list[OAuthProviderConfig]:
    return [
        provider
        for provider in (
            github_provider(),
            google_provider(),
        )
        if provider is not None
    ]

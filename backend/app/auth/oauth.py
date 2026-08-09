from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True, slots=True)
class OAuthProviderConfig:
    provider: str
    client_id: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str | None
    scopes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OAuthAuthorizationRequest:
    url: str
    state: str
    code_verifier: str


def build_pkce_challenge(verifier: str) -> str:
    import base64

    digest = hashlib.sha256(
        verifier.encode("ascii"),
    ).digest()
    return (
        base64.urlsafe_b64encode(digest)
        .decode("ascii")
        .rstrip("=")
    )


def build_authorization_request(
    *,
    config: OAuthProviderConfig,
    redirect_uri: str,
) -> OAuthAuthorizationRequest:
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = build_pkce_challenge(verifier)

    params = {
        "client_id": config.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(config.scopes),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }

    return OAuthAuthorizationRequest(
        url=f"{config.authorization_endpoint}?{urlencode(params)}",
        state=state,
        code_verifier=verifier,
    )

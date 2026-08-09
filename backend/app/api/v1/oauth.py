from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, status

from app.auth.oauth import build_authorization_request
from app.auth.oauth_providers import enabled_oauth_providers
from app.schemas.oauth import OAuthProviderResponse


router = APIRouter(
    prefix="/oauth",
    tags=["OAuth"],
)


@router.get(
    "/providers",
    response_model=list[str],
)
async def list_oauth_providers() -> list[str]:
    return [
        provider.provider
        for provider in enabled_oauth_providers()
    ]


@router.get(
    "/{provider}/authorize",
    response_model=OAuthProviderResponse,
)
async def oauth_authorize(
    provider: str,
) -> OAuthProviderResponse:
    providers = {
        item.provider: item
        for item in enabled_oauth_providers()
    }
    config = providers.get(provider)

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth provider is not configured.",
        )

    base_url = os.getenv(
        "PUBLIC_API_BASE_URL",
        "http://localhost:8000",
    ).rstrip("/")

    request = build_authorization_request(
        config=config,
        redirect_uri=f"{base_url}/api/v1/oauth/{provider}/callback",
    )

    return OAuthProviderResponse(
        provider=config.provider,
        authorization_url=request.url,
        state=request.state,
    )


@router.get("/{provider}/callback")
async def oauth_callback_placeholder(
    provider: str,
    code: str | None = None,
    state: str | None = None,
) -> dict[str, str]:
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth callback requires code and state.",
        )

    return {
        "provider": provider,
        "status": "callback_received",
        "message": (
            "Phase 16 establishes OAuth provider discovery, Authorization "
            "Code + PKCE initiation, and identity persistence schema. "
            "Provider token exchange/account linking must be enabled only "
            "with real provider credentials and callback-state persistence."
        ),
    }

from __future__ import annotations

from pydantic import BaseModel


class OAuthProviderResponse(BaseModel):
    provider: str
    authorization_url: str
    state: str
    pkce: str = "S256"

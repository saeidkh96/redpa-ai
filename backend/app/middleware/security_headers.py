from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.responses import RedirectResponse


class SecurityHeadersMiddleware(
    BaseHTTPMiddleware,
):
    def __init__(
        self,
        app,
        *,
        require_https: bool = False,
    ) -> None:
        super().__init__(
            app,
        )
        self.require_https = require_https

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        forwarded_proto = request.headers.get(
            "x-forwarded-proto",
            request.url.scheme,
        )

        if (
            self.require_https
            and forwarded_proto != "https"
        ):
            return RedirectResponse(
                str(
                    request.url.replace(
                        scheme="https",
                    )
                ),
                status_code=307,
            )

        response = await call_next(
            request,
        )

        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=()"
            ),
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-site",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "font-src 'self' https://cdn.jsdelivr.net data:"
),
        }

        if self.require_https:
            headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"

        for name, value in headers.items():
            response.headers[name] = value

        return response

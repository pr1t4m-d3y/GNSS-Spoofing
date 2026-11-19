"""API-key authentication."""

from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, Request

from .config import Settings


def require_api_key(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency: enforce the ``X-API-Key`` header.

    Authentication fails closed: if no key is configured and auth was not explicitly
    disabled (``GNSS_AUTH_DISABLED=true``), protected routes answer 503.
    """
    settings: Settings = request.app.state.settings
    if settings.auth_disabled:
        return
    if not settings.api_key:
        raise HTTPException(status_code=503, detail="Authentication is not configured.")
    if x_api_key is None or not hmac.compare_digest(
        x_api_key.encode("utf-8"), settings.api_key.encode("utf-8")
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

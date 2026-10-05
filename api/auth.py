from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Enforce X-API-Key on /api/v1 when RIVALRY_API_KEY is set (opt-in)."""
    expected = os.getenv("RIVALRY_API_KEY", "")
    if not expected:
        if os.getenv("RIVALRY_ENV", "").strip().lower() in {"production", "prod"}:
            raise RuntimeError("RIVALRY_API_KEY must be configured in production")
        return
    if not x_api_key or not hmac.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

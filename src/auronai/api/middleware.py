"""Auth and rate-limiting middleware for AuronAI Trading API."""

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address

# ── API Key Auth ─────────────────────────────────────────────────────────

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_VALID_KEYS: set[str] | None = None


def _get_valid_keys() -> set[str] | None:
    global _VALID_KEYS
    if _VALID_KEYS is not None:
        return _VALID_KEYS
    raw = os.getenv("AURONAI_API_KEYS", "").strip()
    if not raw:
        _VALID_KEYS = set()
        return _VALID_KEYS
    _VALID_KEYS = {k.strip() for k in raw.split(",") if k.strip()}
    return _VALID_KEYS


async def verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str | None:
    """Validate X-API-Key header. Skip auth if no keys configured."""
    keys = _get_valid_keys()
    if not keys:
        return None
    if api_key is None or api_key not in keys:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


# ── Rate Limiting ────────────────────────────────────────────────────────

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
)

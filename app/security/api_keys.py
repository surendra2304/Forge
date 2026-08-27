"""
API Key Authentication, Token Verification, and Sliding Window Rate Limiting for Project FORGE.
"""

from collections import defaultdict
import time
from typing import Dict, List, Optional
from fastapi import Header, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.production import production_settings
from app.core.logging import get_logger

logger = get_logger("security.api_keys")

bearer_scheme = HTTPBearer(auto_error=False)


class RateLimiter:
    """Sliding-window request rate limiter per client/API key."""

    def __init__(self, limit_per_hour: int = 100):
        self.limit_per_hour = limit_per_hour
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, identifier: str) -> bool:
        """Check if client identifier is within hourly request threshold."""
        if not production_settings.rate_limit_enabled:
            return True

        now = time.time()
        window_start = now - 3600.0

        # Purge timestamps outside the 1-hour window
        self.requests[identifier] = [ts for ts in self.requests[identifier] if ts > window_start]

        if len(self.requests[identifier]) >= self.limit_per_hour:
            return False

        self.requests[identifier].append(now)
        return True

    def get_remaining(self, identifier: str) -> int:
        """Get remaining allowed requests in current window."""
        now = time.time()
        window_start = now - 3600.0
        active_reqs = [ts for ts in self.requests[identifier] if ts > window_start]
        return max(0, self.limit_per_hour - len(active_reqs))


rate_limiter = RateLimiter(limit_per_hour=production_settings.default_rate_limit)


class APIKeyManager:
    """Validates API credentials and manages key rotations."""

    def __init__(self):
        self.valid_keys: set[str] = set()
        self._sync_keys()

    def _sync_keys(self):
        if production_settings.forge_api_key:
            self.valid_keys.add(production_settings.forge_api_key)

    def add_key(self, key: str):
        self.valid_keys.add(key)

    def revoke_key(self, key: str):
        self.valid_keys.discard(key)

    def validate_key(self, key: Optional[str]) -> bool:
        if self.valid_keys:
            return key in self.valid_keys
        if not production_settings.api_key_required:
            # If no API key requirement is configured and no specific keys loaded, allow request
            return True
        return False


api_key_manager = APIKeyManager()


async def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    bearer_auth: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> str:
    """
    FastAPI security dependency validating incoming API key and enforcing rate limits.
    Accepts credentials via X-API-Key header or Bearer authorization.
    """
    key = x_api_key or (bearer_auth.credentials if bearer_auth else None)

    # Validate authentication
    if not api_key_manager.validate_key(key):
        logger.warning(f"Unauthorized API request attempt from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header or Bearer token.",
        )

    # Rate limiting
    client_id = key or (request.client.host if request.client else "anonymous")
    if not rate_limiter.is_allowed(client_id):
        logger.warning(f"Rate limit exceeded for client '{client_id[:8]}...'")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 100 requests per hour.",
        )

    return client_id

"""
Authentication and Authorization dependencies for Project FORGE API.
Secures FORGE endpoints with API Key verification for FRIDAY delegation and external consumers.
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_api_key(
    x_api_key: Optional[str] = Security(api_key_header),
    auth_cred: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Optional[str]:
    """
    Verify master API Key from X-API-Key header or Authorization: Bearer token.
    If FORGE_API_KEY is not configured in settings, allows unauthenticated local access.
    """
    expected_key = settings.api_key

    if not expected_key:
        # Development mode: No API key configured
        return None

    # Check X-API-Key header
    if x_api_key and x_api_key == expected_key:
        return x_api_key

    # Check Authorization: Bearer token
    if auth_cred and auth_cred.credentials == expected_key:
        return auth_cred.credentials

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Invalid or missing FORGE API Key",
        headers={"WWW-Authenticate": "Bearer"},
    )

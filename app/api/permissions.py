"""
Permission Boundary enforcement for FORGE API.
Ensures FORGE operations remain strictly confined to the task workspace sandbox.
"""

from typing import List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel


class PermissionCheckResult(BaseModel):
    allowed: bool
    scope: str
    message: str


def enforce_permission_boundary(
    permission_scope: str = "sandbox",
    user_authorized: bool = False,
    requested_actions: Optional[List[str]] = None,
) -> PermissionCheckResult:
    """
    Enforces that FORGE operates strictly within its workspace sandbox.
    Any request to modify personal host files, perform external communications,
    or deploy to production without explicit user authorization is blocked with 403.
    """
    scope = (permission_scope or "sandbox").lower().strip()
    actions = requested_actions or []

    # Prohibited dangerous scopes without explicit user authorization
    restricted_scopes = [
        "unrestricted",
        "host_filesystem",
        "personal_files",
        "external_broadcast",
        "production_deploy",
        "root_execution",
    ]

    if scope in restricted_scopes or any(act in restricted_scopes for act in actions):
        if not user_authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Permission Denied: Scope '{scope}' exceeds autonomous workspace sandbox. "
                    "Explicit user / FRIDAY authorization is required."
                ),
            )

    return PermissionCheckResult(
        allowed=True,
        scope=scope,
        message=f"Operation permitted under scope '{scope}'.",
    )

"""
Tool Permissions and Security Allowlist for Project FORGE Execution Engine.
Enforces strict role-based tool authorization and filesystem sandbox confinement.
"""

from enum import Enum
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger("execution.permissions")


class ToolPermission(str, Enum):
    """Granular permissions for tool actions."""

    FS_READ = "fs:read"
    FS_WRITE = "fs:write"
    FS_DELETE = "fs:delete"
    TERMINAL_EXEC = "terminal:exec"
    PROCESS_SPAWN = "process:spawn"
    PROCESS_KILL = "process:kill"
    GIT_READ = "git:read"
    GIT_WRITE = "git:write"
    GIT_COMMIT = "git:commit"
    GIT_PUSH = "git:push"
    PR_CREATE = "pr:create"
    DELIVERY_PACKAGE = "delivery:package"


class PermissionDeniedError(Exception):
    """Raised when an agent attempts an unauthorized tool action."""


class UnauthorizedGitOperationError(PermissionDeniedError):
    """Raised when an unauthorized Git write/commit/PR operation is attempted."""


class UnauthorizedGitPushError(UnauthorizedGitOperationError):
    """Raised when an unauthorized Git push operation is attempted without explicit authorization."""


class SandboxViolationError(Exception):
    """Raised when an agent attempts to access paths outside its workspace sandbox."""


# Default role-to-permissions allowlist mapping
DEFAULT_ROLE_PERMISSIONS: dict[str, set[ToolPermission]] = {
    "planner": {
        ToolPermission.FS_READ,
        ToolPermission.GIT_READ,
    },
    "codebase_analyzer": {
        ToolPermission.FS_READ,
        ToolPermission.FS_WRITE,
        ToolPermission.GIT_READ,
    },
    "architect": {
        ToolPermission.FS_READ,
        ToolPermission.FS_WRITE,
        ToolPermission.GIT_READ,
    },
    "developer": {
        ToolPermission.FS_READ,
        ToolPermission.FS_WRITE,
        ToolPermission.FS_DELETE,
        ToolPermission.TERMINAL_EXEC,
        ToolPermission.PROCESS_SPAWN,
        ToolPermission.PROCESS_KILL,
        ToolPermission.GIT_READ,
        ToolPermission.GIT_WRITE,
    },
    "frontend": {
        ToolPermission.FS_READ,
        ToolPermission.FS_WRITE,
        ToolPermission.FS_DELETE,
        ToolPermission.TERMINAL_EXEC,
        ToolPermission.PROCESS_SPAWN,
        ToolPermission.PROCESS_KILL,
        ToolPermission.GIT_READ,
        ToolPermission.GIT_WRITE,
    },
    "backend": {
        ToolPermission.FS_READ,
        ToolPermission.FS_WRITE,
        ToolPermission.FS_DELETE,
        ToolPermission.TERMINAL_EXEC,
        ToolPermission.PROCESS_SPAWN,
        ToolPermission.PROCESS_KILL,
        ToolPermission.GIT_READ,
        ToolPermission.GIT_WRITE,
    },
    "tester": {
        ToolPermission.FS_READ,
        ToolPermission.FS_WRITE,
        ToolPermission.TERMINAL_EXEC,
        ToolPermission.GIT_READ,
    },
    "debugger": {
        ToolPermission.FS_READ,
        ToolPermission.FS_WRITE,
        ToolPermission.TERMINAL_EXEC,
        ToolPermission.PROCESS_SPAWN,
        ToolPermission.PROCESS_KILL,
        ToolPermission.GIT_READ,
    },
    "security_reviewer": {
        ToolPermission.FS_READ,
        ToolPermission.FS_WRITE,
        ToolPermission.TERMINAL_EXEC,
        ToolPermission.GIT_READ,
    },
    "code_reviewer": {
        ToolPermission.FS_READ,
        ToolPermission.GIT_READ,
    },
    "release_engineer": {
        ToolPermission.FS_READ,
        ToolPermission.FS_WRITE,
        ToolPermission.TERMINAL_EXEC,
        ToolPermission.GIT_READ,
        ToolPermission.GIT_WRITE,
    },
}


class PermissionManager:
    """Enforces immutable permissions and sandbox boundaries for execution tools."""

    def __init__(self, custom_allowlist: dict[str, set[ToolPermission]] | None = None):
        # Freeze default allowlist copy so agents cannot grant themselves permissions at runtime
        self._allowlist: dict[str, set[ToolPermission]] = {
            role: set(perms)
            for role, perms in (custom_allowlist or DEFAULT_ROLE_PERMISSIONS).items()
        }

    def get_role_permissions(self, role_name: str) -> set[ToolPermission]:
        """Return the immutable set of allowed permissions for a role."""
        return set(self._allowlist.get(role_name.lower(), set()))

    def check_permission(self, role_name: str, permission: ToolPermission) -> None:
        """Raise PermissionDeniedError if the role lacks the required permission."""
        allowed = self.get_role_permissions(role_name)
        if permission not in allowed:
            msg = f"Security Violation: Agent role '{role_name}' lacks permission '{permission.value}'"
            logger.warning(msg)
            raise PermissionDeniedError(msg)

    def grant_permission(self, role_name: str, permission: ToolPermission) -> None:
        """Explicitly grant a permission to a role in this manager instance."""
        role_key = role_name.lower()
        if role_key not in self._allowlist:
            self._allowlist[role_key] = set()
        self._allowlist[role_key].add(permission)

    def check_git_commit_authorized(self, authorized: bool) -> None:
        """Raise UnauthorizedGitOperationError if git commit is not explicitly authorized."""
        if not authorized:
            msg = "Security Violation: Git commit requires explicit authorization"
            logger.warning(msg)
            raise UnauthorizedGitOperationError(msg)

    def check_git_push_authorized(
        self, authorized: bool, push_token: str | None = None
    ) -> None:
        """Raise UnauthorizedGitPushError if git push is not explicitly authorized."""
        if not authorized and not push_token:
            msg = "Security Violation: Git push requires explicit separate authorization"
            logger.warning(msg)
            raise UnauthorizedGitPushError(msg)

    def validate_sandbox_path(self, target_path: Path, sandbox_root: Path) -> Path:
        """
        Ensure resolved target_path strictly resides within the sandbox_root directory.
        Raises SandboxViolationError on path traversal attempts.
        """
        resolved_sandbox = sandbox_root.resolve()
        resolved_target = (
            sandbox_root / target_path if not target_path.is_absolute() else target_path
        ).resolve()

        try:
            resolved_target.relative_to(resolved_sandbox)
        except ValueError as exc:
            msg = f"Sandbox Violation: Path '{target_path}' escapes sandbox root '{sandbox_root}'"
            logger.error(msg)
            raise SandboxViolationError(msg) from exc

        return resolved_target


permission_manager = PermissionManager()

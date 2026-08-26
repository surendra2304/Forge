"""
Unified Execution Engine for Project FORGE.
Dispatches filesystem, terminal, process, and git actions while enforcing permission boundaries.
"""

from app.core.logging import get_logger
from app.core.workspace import WorkspaceManager, workspace_manager
from app.execution.filesystem import FilesystemTool
from app.execution.git_tool import GitTool
from app.execution.github import GitHubTool
from app.execution.permissions import (
    PermissionManager,
    ToolPermission,
    permission_manager,
)
from app.execution.process_manager import ProcessManagerTool
from app.execution.terminal import TerminalTool

logger = get_logger("execution.engine")


class ExecutionEngine:
    """Central execution engine orchestrating sandboxed tools with permission gating."""

    def __init__(
        self,
        wm: WorkspaceManager | None = None,
        pm: PermissionManager | None = None,
    ):
        self.wm = wm or workspace_manager
        self.pm = pm or permission_manager
        self.fs = FilesystemTool(wm=self.wm, pm=self.pm)
        self.terminal = TerminalTool(wm=self.wm, pm=self.pm)
        self.process = ProcessManagerTool(wm=self.wm, pm=self.pm)
        self.git = GitTool(wm=self.wm, pm=self.pm)
        self.github = GitHubTool(wm=self.wm, pm=self.pm, git=self.git)

    def check_permission(self, role: str, permission: ToolPermission) -> None:
        """Check role permissions."""
        self.pm.check_permission(role, permission)


execution_engine = ExecutionEngine()

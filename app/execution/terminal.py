"""
Terminal Tool for Project FORGE Execution Engine.
Executes sandboxed shell commands with timeout enforcement, output streaming, and exit code capture.
"""

import asyncio
import os
from pathlib import Path
import time
from typing import Dict, Optional
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.core.workspace import WorkspaceManager, workspace_manager
from app.execution.permissions import (
    PermissionManager,
    ToolPermission,
    permission_manager,
)

logger = get_logger("execution.terminal")


class CommandResult(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    cwd: str


class TerminalTool:
    """Provides sandboxed command execution in the task's project directory."""

    def __init__(
        self,
        wm: Optional[WorkspaceManager] = None,
        pm: Optional[PermissionManager] = None,
    ):
        self.wm = wm or workspace_manager
        self.pm = pm or permission_manager

    async def run_command(
        self,
        task_id: str,
        command: str,
        timeout_seconds: int = 60,
        env_vars: Optional[Dict[str, str]] = None,
        role: str = "developer",
    ) -> CommandResult:
        """
        Execute command inside the task's project directory.
        """
        self.pm.check_permission(role, ToolPermission.TERMINAL_EXEC)

        paths = self.wm.get_workspace_paths(task_id) or self.wm.create_workspace(task_id)
        cwd = paths.project.resolve()

        custom_env = os.environ.copy()
        if env_vars:
            custom_env.update(env_vars)

        start_time = time.perf_counter()
        timed_out = False
        stdout_text = ""
        stderr_text = ""
        exit_code = -1

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env=custom_env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout_seconds
                )
                exit_code = process.returncode if process.returncode is not None else 0
                stdout_text = stdout_bytes.decode("utf-8", errors="replace")
                stderr_text = stderr_bytes.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                timed_out = True
                try:
                    process.kill()
                except Exception:
                    pass
                exit_code = -9
                stderr_text = f"Command timed out after {timeout_seconds} seconds"

        except Exception as e:
            logger.error(f"Error executing command '{command}' in task {task_id}: {e}")
            stderr_text = str(e)
            exit_code = 1

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Append command execution record to workspace logs
        log_entry = (
            f"--- [CMD] {command} (exit={exit_code}, duration={duration_ms:.1f}ms) ---\n"
            f"STDOUT:\n{stdout_text}\n"
            f"STDERR:\n{stderr_text}\n"
        )
        self.wm.append_log(task_id, "terminal.log", log_entry)

        return CommandResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout_text,
            stderr=stderr_text,
            duration_ms=round(duration_ms, 2),
            timed_out=timed_out,
            cwd=str(cwd),
        )

    async def install_dependencies(
        self,
        task_id: str,
        timeout_seconds: int = 120,
        role: str = "developer",
    ) -> CommandResult:
        """
        Inspect the project workspace and install project dependencies using the appropriate package manager:
        - Node.js / TypeScript: npm install (or yarn install)
        - Go: go mod tidy
        - Python: pip install -r requirements.txt
        """
        paths = self.wm.get_workspace_paths(task_id) or self.wm.create_workspace(task_id)
        project_dir = paths.project

        if (project_dir / "package.json").exists():
            cmd = "yarn install" if (project_dir / "yarn.lock").exists() else "npm install"
            return await self.run_command(task_id, cmd, timeout_seconds=timeout_seconds, role=role)
        elif (project_dir / "go.mod").exists():
            return await self.run_command(task_id, "go mod tidy", timeout_seconds=timeout_seconds, role=role)
        elif (project_dir / "requirements.txt").exists():
            return await self.run_command(task_id, "pip install -r requirements.txt", timeout_seconds=timeout_seconds, role=role)

        return CommandResult(
            command="install_dependencies",
            exit_code=0,
            stdout="No recognized manifest (package.json, go.mod, requirements.txt) found.",
            stderr="",
            duration_ms=0.1,
            timed_out=False,
            cwd=str(project_dir),
        )

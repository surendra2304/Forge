"""
Workspace Manager for Project FORGE.
Handles isolated workspace provisioning, directory hierarchies, path resolution, and artifact management.
"""

from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("core.workspace")


class WorkspacePaths(BaseModel):
    """Encapsulates all standard subdirectories of an isolated task workspace."""
    root: Path
    project: Path
    artifacts: Path
    logs: Path
    state: Path
    cache: Path

    model_config = {"arbitrary_types_allowed": True}

    def to_dict(self) -> Dict[str, str]:
        return {
            "root": str(self.root.resolve()),
            "project": str(self.project.resolve()),
            "artifacts": str(self.artifacts.resolve()),
            "logs": str(self.logs.resolve()),
            "state": str(self.state.resolve()),
            "cache": str(self.cache.resolve()),
        }


class WorkspaceManager:
    """Manages creation, resolution, and lifecycle of task-specific filesystem sandboxes."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def get_task_workspace_dir(self, task_id: str) -> Path:
        """Return the root path for a given task ID."""
        # Sanitize task_id prefix if needed
        folder_name = task_id if task_id.startswith("task_") else f"task_{task_id}"
        base_workspaces = self.settings.base_dir / self.settings.workspaces_dir
        return base_workspaces / folder_name

    def create_workspace(
        self,
        task_id: str,
        custom_base: Optional[Path] = None,
        repo_url: Optional[str] = None,
        local_path: Optional[str | Path] = None,
    ) -> WorkspacePaths:
        """
        Create isolated directory hierarchy for task under workspaces/task_<id>/:
        - project/ (optionally cloned from repo_url or copied from local_path)
        - artifacts/
        - logs/
        - state/
        - cache/
        """
        import subprocess

        root_dir = (
            custom_base
            if custom_base
            else self.get_task_workspace_dir(task_id)
        )

        subdirs = {
            "project": root_dir / "project",
            "artifacts": root_dir / "artifacts",
            "logs": root_dir / "logs",
            "state": root_dir / "state",
            "cache": root_dir / "cache",
        }

        # Create root and all subdirectories
        root_dir.mkdir(parents=True, exist_ok=True)
        for name, path in subdirs.items():
            if name != "project":
                path.mkdir(parents=True, exist_ok=True)

        # Populate project directory from repo_url, local_path, or create empty
        if repo_url:
            logger.info(f"Cloning repository '{repo_url}' into task workspace {task_id}...")
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, str(subdirs["project"])],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                logger.info(f"Successfully cloned repository into {subdirs['project']}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone repository '{repo_url}': {e.stderr}")
                subdirs["project"].mkdir(parents=True, exist_ok=True)
                raise RuntimeError(f"Git clone failed for '{repo_url}': {e.stderr}") from e
        elif local_path:
            src_path = Path(local_path).resolve()
            logger.info(f"Copying local codebase from '{src_path}' into task workspace {task_id}...")
            if not src_path.exists():
                raise FileNotFoundError(f"Local codebase path does not exist: {src_path}")
            subdirs["project"].mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_path, subdirs["project"], dirs_exist_ok=True)
            logger.info(f"Successfully copied local codebase from '{src_path}' into {subdirs['project']}")
        else:
            subdirs["project"].mkdir(parents=True, exist_ok=True)

        # Write metadata manifest
        manifest_file = root_dir / ".forge_workspace"
        manifest_content = (
            f"task_id: {task_id}\n"
            f"initialized: true\n"
            f"repo_url: {repo_url or 'none'}\n"
            f"local_path: {str(local_path) if local_path else 'none'}\n"
            f"subdirs: [project, artifacts, logs, state, cache]\n"
        )
        manifest_file.write_text(manifest_content, encoding="utf-8")

        paths = WorkspacePaths(
            root=root_dir,
            project=subdirs["project"],
            artifacts=subdirs["artifacts"],
            logs=subdirs["logs"],
            state=subdirs["state"],
            cache=subdirs["cache"],
        )
        logger.info(f"Initialized isolated task workspace at {root_dir}")
        return paths

    def get_workspace_paths(self, task_id: str) -> Optional[WorkspacePaths]:
        """Resolve workspace paths for an existing task."""
        root_dir = self.get_task_workspace_dir(task_id)
        if not root_dir.exists():
            return None

        return WorkspacePaths(
            root=root_dir,
            project=root_dir / "project",
            artifacts=root_dir / "artifacts",
            logs=root_dir / "logs",
            state=root_dir / "state",
            cache=root_dir / "cache",
        )

    def write_project_file(self, task_id: str, relative_path: str, content: str) -> Path:
        """Safely write a file inside the task's project directory."""
        paths = self.get_workspace_paths(task_id) or self.create_workspace(task_id)
        target = (paths.project / relative_path).resolve()

        # Prevent directory traversal outside project dir
        if not str(target).startswith(str(paths.project.resolve())):
            raise ValueError(f"Path traversal detected: {relative_path}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def read_project_file(self, task_id: str, relative_path: str) -> Optional[str]:
        """Safely read a file from the task's project directory."""
        paths = self.get_workspace_paths(task_id)
        if not paths:
            return None
        target = (paths.project / relative_path).resolve()
        if not str(target).startswith(str(paths.project.resolve())) or not target.exists():
            return None
        return target.read_text(encoding="utf-8")

    def save_artifact(self, task_id: str, artifact_name: str, content: bytes | str) -> Path:
        """Save a generated artifact to the task's artifacts directory."""
        paths = self.get_workspace_paths(task_id) or self.create_workspace(task_id)
        target = (paths.artifacts / artifact_name).resolve()

        if not str(target).startswith(str(paths.artifacts.resolve())):
            raise ValueError(f"Invalid artifact path: {artifact_name}")

        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            target.write_bytes(content)
        return target

    def append_log(self, task_id: str, log_filename: str, log_message: str) -> None:
        """Append log line to specified log file in logs directory."""
        paths = self.get_workspace_paths(task_id) or self.create_workspace(task_id)
        log_file = paths.logs / log_filename
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_message.rstrip() + "\n")

    def cleanup_workspace(self, task_id: str) -> bool:
        """Safely remove a task workspace directory."""
        root_dir = self.get_task_workspace_dir(task_id)
        if root_dir.exists():
            shutil.rmtree(root_dir, ignore_errors=True)
            logger.info(f"Cleaned up workspace at {root_dir}")
            return True
        return False


workspace_manager = WorkspaceManager()

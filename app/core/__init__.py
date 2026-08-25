"""
Core module for Project FORGE.
"""

from app.core.analyzer import TaskAnalysisResult, TaskAnalyzer, task_analyzer
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, setup_logging
from app.core.orchestrator import OrchestratorCore, orchestrator
from app.core.workspace import WorkspaceManager, WorkspacePaths, workspace_manager

__all__ = [
    "Settings",
    "get_settings",
    "setup_logging",
    "get_logger",
    "WorkspaceManager",
    "WorkspacePaths",
    "workspace_manager",
    "TaskAnalyzer",
    "TaskAnalysisResult",
    "task_analyzer",
    "OrchestratorCore",
    "orchestrator",
]

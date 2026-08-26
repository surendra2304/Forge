"""
Core module for Project FORGE.
"""

from app.core.analyzer import TaskAnalysisResult, TaskAnalyzer, task_analyzer
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, setup_logging
from app.core.orchestrator import OrchestratorCore, orchestrator
from app.core.workspace import WorkspaceManager, WorkspacePaths, workspace_manager

__all__ = [
    "OrchestratorCore",
    "Settings",
    "TaskAnalysisResult",
    "TaskAnalyzer",
    "WorkspaceManager",
    "WorkspacePaths",
    "get_logger",
    "get_settings",
    "orchestrator",
    "setup_logging",
    "task_analyzer",
    "workspace_manager",
]

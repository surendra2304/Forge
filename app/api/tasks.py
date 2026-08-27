"""
Enhanced Task Management API for Project FORGE & FRIDAY Integration.
Provides full task lifecycle, inspection, logging, artifact download, cancellation, and soft-archive endpoints.
"""

import json
import mimetypes
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.agents.project_types import detect_project_type
from app.api.schemas import (
    ArtifactResponse,
    FileInspection,
    LogEntry,
    TaskActionRequest,
    TaskActionResponse,
    TaskCreateRequest,
    TaskDetailResponse,
    TaskInspectResponse,
    TaskLogsResponse,
    TaskResponse,
    TaskSummaryResponse,
)
from app.api.websocket import ws_manager
from app.core.logging import get_logger
from app.core.orchestrator import OrchestratorCore
from app.core.progress_tracker import ProgressTracker
from app.core.workspace import workspace_manager
from app.execution.dependency_manager import DependencyManager
from app.memory.db import db_manager
from app.memory.models import TaskState
from app.memory.state_store import StateStore
from app.memory.task_lifecycle import InvalidStateTransitionError, TaskStateMachine

logger = get_logger("api.tasks")
tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])


def get_state_store() -> StateStore:
    return StateStore(db_manager)


def get_task_lifecycle(store: StateStore = Depends(get_state_store)) -> TaskStateMachine:
    return TaskStateMachine(store)


def get_orchestrator(store: StateStore = Depends(get_state_store)) -> OrchestratorCore:
    return OrchestratorCore(store=store)


@tasks_router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, summary="Submit Engineering Task")
async def create_task(
    request: TaskCreateRequest,
    orchestrator: OrchestratorCore = Depends(get_orchestrator),
    store: StateStore = Depends(get_state_store),
) -> TaskResponse:
    """Intake, analyze, and provision a new autonomous engineering task."""
    metadata = {}
    if request.task_metadata:
        metadata = request.task_metadata.model_dump(mode="json")
    else:
        metadata = {"source": "friday", "priority": "normal", "tags": [], "archived": False}

    task, _ = await orchestrator.intake_and_plan(
        goal=request.goal,
        requirements=request.requirements,
        mode=request.mode,
        repo_url=request.repo_url,
        local_path=request.local_path,
        max_budget=request.max_budget,
    )

    # Attach FRIDAY metadata
    task.metadata.update(metadata)
    await store.save_task(task)

    # Initialize progress tracker for task
    ptype = detect_project_type(task.goal, task.requirements).category.value
    ProgressTracker.get_or_create(task.id, project_type=ptype)

    # Broadcast task creation via WebSocket
    await ws_manager.broadcast_global({
        "event": "task.created",
        "task_id": task.id,
        "goal": task.goal,
        "state": task.state.value,
        "metadata": task.metadata,
    })

    return TaskResponse(
        id=task.id,
        goal=task.goal,
        requirements=task.requirements,
        mode=task.mode,
        workspace_path=task.workspace_path,
        max_budget=task.max_budget,
        budget_consumed=task.budget_consumed,
        state=task.state,
        progress_percentage=task.progress_percentage,
        error_message=task.error_message,
        metadata=task.metadata,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@tasks_router.get("", response_model=list[TaskSummaryResponse], summary="List Tasks")
async def list_tasks(
    status: TaskState | None = Query(default=None, description="Filter by lifecycle state"),
    limit: int = Query(default=50, ge=1, le=500, description="Max tasks to return"),
    since_timestamp: datetime | None = Query(default=None, description="Filter tasks updated after timestamp"),
    include_archived: bool = Query(default=False, description="Include soft-archived tasks"),
    store: StateStore = Depends(get_state_store),
) -> list[TaskSummaryResponse]:
    """Retrieve summarized list of engineering tasks with optional status and time filtering."""
    tasks = await store.list_tasks(state=status, limit=limit)
    summaries = []

    for t in tasks:
        is_archived = t.metadata.get("archived", False)
        if not include_archived and is_archived:
            continue

        if since_timestamp and t.updated_at and t.updated_at < since_timestamp:
            continue

        ptype = detect_project_type(t.goal, t.requirements).category.value
        priority = t.metadata.get("priority", "normal")

        summaries.append(
            TaskSummaryResponse(
                id=t.id,
                goal=t.goal,
                state=t.state,
                progress_percentage=t.progress_percentage,
                project_type=ptype,
                priority=priority,
                created_at=t.created_at,
                updated_at=t.updated_at,
                archived=is_archived,
            )
        )

    return summaries


@tasks_router.get("/{task_id}", response_model=TaskDetailResponse, summary="Get Task Details & ETA")
async def get_task(
    task_id: str,
    store: StateStore = Depends(get_state_store),
) -> TaskDetailResponse:
    """Retrieve fine-grained task status, current DAG stage, and dynamic ETA estimation."""
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")

    paths = workspace_manager.get_workspace_paths(task_id)
    workspace_dirs = {}
    if paths:
        workspace_dirs = {
            "root": str(paths.root),
            "project": str(paths.project),
            "artifacts": str(paths.artifacts),
            "logs": str(paths.logs),
            "state": str(paths.state),
            "cache": str(paths.cache),
        }

    # Retrieve progress tracker snapshot if active
    tracker = ProgressTracker.get_tracker(task_id)
    current_stage = None
    est_remaining = None
    est_completion = None
    if tracker:
        snapshot = tracker.get_snapshot()
        current_stage = snapshot.current_stage.value
        est_remaining = snapshot.estimated_remaining_seconds
        est_completion = snapshot.estimated_completion_at

    # Check fallback stub flag or provenance
    provenance_summary = task.metadata.get("provenance_summary")
    if not provenance_summary and paths and (paths.state / "FALLBACK_STUB.json").exists():
        provenance_summary = "Fallback Stub Generation Detected"

    checkpoints = await store.list_checkpoints(task_id)
    latest_cp = checkpoints[0].id if checkpoints else None

    return TaskDetailResponse(
        id=task.id,
        goal=task.goal,
        requirements=task.requirements,
        mode=task.mode,
        workspace_path=task.workspace_path,
        max_budget=task.max_budget,
        budget_consumed=task.budget_consumed,
        state=task.state,
        progress_percentage=task.progress_percentage,
        error_message=task.error_message,
        metadata=task.metadata,
        workspace_dirs=workspace_dirs,
        current_stage=current_stage,
        estimated_remaining_seconds=est_remaining,
        estimated_completion_at=est_completion,
        provenance_summary=provenance_summary,
        latest_checkpoint_id=latest_cp,
        checkpoints_count=len(checkpoints),
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@tasks_router.get("/{task_id}/logs", response_model=TaskLogsResponse, summary="Get Structured Execution Logs")
async def get_task_logs(
    task_id: str,
    level: str | None = Query(default=None, description="Filter log level (DEBUG, INFO, WARNING, ERROR)"),
    tail_lines: int = Query(default=100, ge=1, le=1000, description="Number of recent log lines"),
    since_timestamp: str | None = Query(default=None, description="Filter log lines since ISO timestamp"),
    store: StateStore = Depends(get_state_store),
) -> TaskLogsResponse:
    """Retrieve structured execution and build logs from task sandbox."""
    paths = workspace_manager.get_workspace_paths(task_id)
    if not paths or not paths.logs.exists():
        return TaskLogsResponse(task_id=task_id, total_lines=0, logs=[])

    log_files = list(paths.logs.glob("*.log"))
    entries: list[LogEntry] = []

    for lf in log_files:
        try:
            lines = lf.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines:
                if not line.strip():
                    continue

                # Infer log level
                entry_level = "INFO"
                if "DEBUG" in line.upper():
                    entry_level = "DEBUG"
                elif "WARNING" in line.upper() or "WARN" in line.upper():
                    entry_level = "WARNING"
                elif "ERROR" in line.upper() or "FAIL" in line.upper() or "EXCEPTION" in line.upper():
                    entry_level = "ERROR"

                if level and entry_level != level.upper():
                    continue

                entries.append(LogEntry(
                    timestamp=None,
                    level=entry_level,
                    message=line,
                ))
        except Exception:
            pass

    selected = entries[-tail_lines:] if len(entries) > tail_lines else entries
    return TaskLogsResponse(
        task_id=task_id,
        total_lines=len(entries),
        logs=selected,
    )


@tasks_router.get("/{task_id}/inspect", response_model=TaskInspectResponse, summary="Deep Task Inspection")
async def inspect_task(
    task_id: str,
    store: StateStore = Depends(get_state_store),
) -> TaskInspectResponse:
    """Perform deep inspection of files, verification breakdown, dependencies, and artifacts."""
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")

    paths = workspace_manager.get_workspace_paths(task_id)
    files_created: list[FileInspection] = []
    artifacts_list: list[str] = []
    dependencies: list[str] = []
    verification_summary = {}

    if paths:
        # Inspect created project files
        if paths.project.exists():
            for f in paths.project.glob("**/*"):
                if f.is_file():
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        lines = len(content.splitlines())
                        files_created.append(FileInspection(
                            path=str(f.relative_to(paths.project)),
                            size_bytes=f.stat().st_size,
                            lines_count=lines,
                        ))
                    except Exception:
                        pass

            # Detect dependencies
            dep_mgr = DependencyManager()
            dependencies = sorted(list(dep_mgr.detect_workspace_dependencies(paths.project)))

        # Inspect artifacts
        if paths.artifacts.exists():
            for art in paths.artifacts.glob("*"):
                if art.is_file():
                    artifacts_list.append(art.name)

        # Inspect verification reports
        report_file = paths.artifacts / "completion_report.json"
        if report_file.exists():
            try:
                data = json.loads(report_file.read_text(encoding="utf-8"))
                verification_summary = data.get("verification_summary", {})
            except Exception:
                pass

    provenance = task.metadata.get("provenance", {})

    return TaskInspectResponse(
        task_id=task.id,
        goal=task.goal,
        state=task.state,
        files_created=files_created,
        verification_summary=verification_summary,
        dependencies=dependencies,
        artifacts=artifacts_list,
        provenance=provenance,
    )


@tasks_router.get("/{task_id}/artifacts", response_model=list[ArtifactResponse], summary="List Downloadable Artifacts")
async def list_task_artifacts(
    task_id: str,
    store: StateStore = Depends(get_state_store),
) -> list[ArtifactResponse]:
    """List all available delivery and verification artifacts for a task."""
    paths = workspace_manager.get_workspace_paths(task_id)
    if not paths or not paths.artifacts.exists():
        return []

    results = []
    for art in paths.artifacts.glob("*"):
        if art.is_file():
            mime, _ = mimetypes.guess_type(art.name)
            results.append(
                ArtifactResponse(
                    id=art.stem,
                    task_id=task_id,
                    name=art.name,
                    path=str(art),
                    file_type=mime or "application/octet-stream",
                    size_bytes=art.stat().st_size,
                    created_at=datetime.fromtimestamp(art.stat().st_ctime),
                )
            )

    return results


@tasks_router.get("/{task_id}/artifacts/{filename}", summary="Download Artifact File")
async def download_task_artifact(
    task_id: str,
    filename: str,
):
    """Download a specific artifact file (e.g. completion report, screenshot)."""
    paths = workspace_manager.get_workspace_paths(task_id)
    if not paths or not paths.artifacts.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifacts directory not found.")

    artifact_file = paths.artifacts / filename
    if not artifact_file.exists() or not artifact_file.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact '{filename}' not found.")

    mime, _ = mimetypes.guess_type(filename)
    return FileResponse(
        path=str(artifact_file),
        filename=filename,
        media_type=mime or "application/octet-stream",
    )


@tasks_router.post("/{task_id}/cancel", response_model=TaskActionResponse, summary="Cancel Running Task")
async def cancel_task(
    task_id: str,
    request: TaskActionRequest | None = None,
    lifecycle: TaskStateMachine = Depends(get_task_lifecycle),
    store: StateStore = Depends(get_state_store),
) -> TaskActionResponse:
    """Gracefully cancel a running task and cleanup background resources."""
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")

    prev_state = task.state
    reason = request.reason if request else "Cancelled via FRIDAY management API"

    try:
        updated_task = await lifecycle.transition(
            task_id=task_id,
            to_state=TaskState.CANCELLED,
            reason=reason,
        )

        # Notify progress tracker and WebSockets
        tracker = ProgressTracker.get_tracker(task_id)
        if tracker:
            await tracker.complete_task(success=False, error=reason)

        await ws_manager.broadcast_to_task(task_id, {
            "event": "task.cancelled",
            "task_id": task_id,
            "previous_state": prev_state.value,
            "current_state": TaskState.CANCELLED.value,
            "reason": reason,
        })
        await ws_manager.broadcast_global({
            "event": "task.cancelled",
            "task_id": task_id,
            "reason": reason,
        })

        return TaskActionResponse(
            task_id=task_id,
            previous_state=prev_state,
            current_state=TaskState.CANCELLED,
            message=f"Task cancelled successfully: {reason}",
            checkpoint_id=None,
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@tasks_router.delete("/{task_id}", summary="Archive Task (Soft Delete)")
async def archive_task(
    task_id: str,
    store: StateStore = Depends(get_state_store),
):
    """Soft-archive a task while preserving all sandbox files on disk."""
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")

    task.metadata["archived"] = True
    task.metadata["archived_at"] = datetime.now().isoformat()
    await store.save_task(task)

    logger.info(f"Task '{task_id}' archived successfully.")
    return {
        "status": "success",
        "task_id": task_id,
        "archived": True,
        "message": f"Task '{task_id}' has been archived and removed from active task listings.",
    }

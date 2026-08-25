"""
API Routes for Project FORGE.
Implements endpoints for Tasks, Workspaces, Lifecycle Actions, Runs/Audit Events, Artifacts, Agents, and Capabilities.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.agents.registry import AgentCapability, agent_registry
from app.api.schemas import (
    ArtifactResponse,
    AuditEventResponse,
    EngineCapabilitiesResponse,
    HealthResponse,
    RunAuditResponse,
    TaskActionRequest,
    TaskActionResponse,
    TaskCreateRequest,
    TaskDetailResponse,
    TaskResponse,
    TimelineEvent,
    TimelineResponse,
)
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.orchestrator import OrchestratorCore, orchestrator
from app.core.workspace import WorkspaceManager, workspace_manager
from app.execution.delivery import DeliveryPackager, delivery_packager
from app.memory.db import db_manager
from app.memory.models import (
    ArtifactRecord,
    ProjectWorkspace,
    TaskEntity,
    TaskMode,
    TaskState,
)
from app.memory.state_store import StateStore
from app.memory.task_lifecycle import InvalidStateTransitionError, TaskStateMachine
from app.providers.base import ProviderCapabilities, ProviderHealthStatus
from app.providers.direct import DirectProvider

logger = get_logger("api.routes")
router = APIRouter()


# --- Dependencies ---

def get_state_store() -> StateStore:
    return StateStore(db_manager)


def get_task_lifecycle(store: StateStore = Depends(get_state_store)) -> TaskStateMachine:
    return TaskStateMachine(store)


def get_default_provider(settings: Settings = Depends(get_settings)) -> DirectProvider:
    return DirectProvider(model_name=settings.default_model)


def get_orchestrator(store: StateStore = Depends(get_state_store)) -> OrchestratorCore:
    return OrchestratorCore(store=store)


def get_workspace_manager() -> WorkspaceManager:
    return workspace_manager


# --- System & Diagnostics ---

@router.get("/health", response_model=HealthResponse, summary="System Health & Diagnostic Check")
async def health_check(
    settings: Settings = Depends(get_settings),
    provider: DirectProvider = Depends(get_default_provider),
) -> HealthResponse:
    """Check database connectivity and provider health status."""
    db_connected = False
    try:
        async with db_manager.connection() as conn:
            async with conn.execute("SELECT 1") as cursor:
                row = await cursor.fetchone()
                if row and row[0] == 1:
                    db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_connected = False

    provider_health = await provider.health()
    capabilities = provider.capabilities()
    overall_status = "healthy" if (db_connected and provider_health.healthy) else "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.env,
        database_connected=db_connected,
        default_provider=provider_health,
        capabilities=capabilities,
    )


@router.get("/capabilities", response_model=EngineCapabilitiesResponse, summary="Get FORGE Capabilities")
async def get_capabilities(
    settings: Settings = Depends(get_settings),
    provider: DirectProvider = Depends(get_default_provider),
) -> EngineCapabilitiesResponse:
    """Return engine, lifecycle, mode, and provider capabilities."""
    return EngineCapabilitiesResponse(
        engine_name=settings.app_name,
        version=settings.app_version,
        supported_modes=[m.value for m in TaskMode],
        lifecycle_states=[s.value for s in TaskState],
        features={
            "isolated_workspaces": True,
            "checkpointing_recovery": True,
            "audit_trail_logging": True,
            "structured_output": True,
            "streaming_telemetry": True,
        },
        provider=provider.capabilities(),
    )


@router.get("/agents", response_model=List[AgentCapability], summary="List Engineering Agent Capabilities")
async def list_agents() -> List[AgentCapability]:
    """Return available engineering agent personas and their tool/task specializations."""
    return agent_registry.list_all()


# --- Task Operations ---

@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and Initialize Engineering Task",
)
async def create_task(
    request: TaskCreateRequest,
    settings: Settings = Depends(get_settings),
    orchestrator: OrchestratorCore = Depends(get_orchestrator),
) -> TaskResponse:
    """
    Create a new engineering task, initialize its isolated workspace,
    run Task Analyzer, synthesize 8-stage TaskGraph DAG, and transition to READY.
    """
    created_task, _ = await orchestrator.intake_and_plan(
        goal=request.goal,
        requirements=request.requirements,
        mode=request.mode,
        max_budget=request.max_budget,
        custom_workspace=request.workspace,
    )

    return TaskResponse(
        id=created_task.id,
        goal=created_task.goal,
        requirements=created_task.requirements,
        mode=created_task.mode,
        workspace_path=created_task.workspace_path,
        max_budget=created_task.max_budget,
        budget_consumed=created_task.budget_consumed,
        state=created_task.state,
        progress_percentage=created_task.progress_percentage,
        error_message=created_task.error_message,
        created_at=created_task.created_at,
        updated_at=created_task.updated_at,
    )


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse, summary="Inspect Task Progress & State")
async def get_task(
    task_id: str,
    store: StateStore = Depends(get_state_store),
) -> TaskDetailResponse:
    """Retrieve full task status, progress, budget consumed, and workspace paths."""
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")

    ws_paths = workspace_manager.get_workspace_paths(task_id) or workspace_manager.create_workspace(task_id)
    checkpoints = await store.list_checkpoints(task_id)
    latest_cp = checkpoints[-1] if checkpoints else None

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
        created_at=task.created_at,
        updated_at=task.updated_at,
        workspace_dirs=ws_paths.to_dict(),
        latest_checkpoint_id=latest_cp.id if latest_cp else None,
        checkpoints_count=len(checkpoints),
    )


@router.post("/tasks/{task_id}/pause", response_model=TaskActionResponse, summary="Pause Running Task")
async def pause_task(
    task_id: str,
    action: Optional[TaskActionRequest] = None,
    lifecycle: TaskStateMachine = Depends(get_task_lifecycle),
    store: StateStore = Depends(get_state_store),
) -> TaskActionResponse:
    """Pause task execution and create a recoverable checkpoint."""
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")

    reason = action.reason if action and action.reason else "User requested pause"
    prev_state = task.state

    try:
        updated_task, checkpoint = await lifecycle.pause(task_id=task_id, reason=reason)
        return TaskActionResponse(
            task_id=task_id,
            previous_state=prev_state,
            current_state=updated_task.state,
            message="Task paused successfully and checkpoint created",
            checkpoint_id=checkpoint.id,
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/tasks/{task_id}/resume", response_model=TaskActionResponse, summary="Resume Paused Task")
async def resume_task(
    task_id: str,
    action: Optional[TaskActionRequest] = None,
    lifecycle: TaskStateMachine = Depends(get_task_lifecycle),
    store: StateStore = Depends(get_state_store),
) -> TaskActionResponse:
    """Resume task execution from its most recent checkpoint."""
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")

    reason = action.reason if action and action.reason else "User requested resume"
    prev_state = task.state

    try:
        updated_task, checkpoint = await lifecycle.resume(task_id=task_id, reason=reason)
        return TaskActionResponse(
            task_id=task_id,
            previous_state=prev_state,
            current_state=updated_task.state,
            message="Task resumed from checkpoint",
            checkpoint_id=checkpoint.id if checkpoint else None,
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/tasks/{task_id}/cancel", response_model=TaskActionResponse, summary="Cancel Task")
async def cancel_task(
    task_id: str,
    action: Optional[TaskActionRequest] = None,
    lifecycle: TaskStateMachine = Depends(get_task_lifecycle),
    store: StateStore = Depends(get_state_store),
) -> TaskActionResponse:
    """Cancel task execution and mark as CANCELLED."""
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")

    reason = action.reason if action and action.reason else "User requested cancel"
    prev_state = task.state

    try:
        updated_task = await lifecycle.cancel(task_id=task_id, reason=reason)
        return TaskActionResponse(
            task_id=task_id,
            previous_state=prev_state,
            current_state=updated_task.state,
            message="Task cancelled successfully",
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --- Runs / Audit Events ---

@router.get("/runs/{run_id}", response_model=RunAuditResponse, summary="Get Run Audit Trail")
async def get_run_audit_trail(
    run_id: str,
    store: StateStore = Depends(get_state_store),
) -> RunAuditResponse:
    """Retrieve chronological audit trail of structured events for a task/run."""
    events = await store.get_audit_trail(run_id)
    return RunAuditResponse(
        task_id=run_id,
        total_events=len(events),
        events=[
            AuditEventResponse(
                id=e.id,
                task_id=e.task_id,
                event_type=e.event_type,
                payload=e.payload,
                timestamp=e.timestamp,
            )
            for e in events
        ],
    )


@router.get("/tasks/{task_id}/timeline", response_model=TimelineResponse, summary="Get Structured Chronological Task Timeline")
async def get_task_timeline(
    task_id: str,
    store: StateStore = Depends(get_state_store),
) -> TimelineResponse:
    """
    Return a standardized, chronological telemetry stream of all task actions,
    stages, model invocations, and checkpoints for external dashboard consumption (FRIDAY / AI Universe).
    """
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")

    events = await store.get_audit_trail(task_id)
    timeline_events: List[TimelineEvent] = []
    stages_covered = set()

    for e in events:
        payload = e.payload or {}
        stage = payload.get("stage", "Execution")
        stages_covered.add(stage)

        timeline_events.append(
            TimelineEvent(
                id=e.id,
                task_id=e.task_id,
                run_id=payload.get("run_id", e.id),
                stage=stage,
                agent_id=payload.get("agent_id", payload.get("agent", "orchestrator")),
                provider_model=payload.get("provider_model", "direct-model"),
                action=e.event_type,
                inputs=payload.get("inputs", {k: v for k, v in payload.items() if k not in ["stage", "run_id", "agent_id", "provider_model", "result", "duration_ms", "checkpoint_id"]}),
                result=payload.get("result"),
                duration_ms=payload.get("duration_ms", 0.0),
                checkpoint_id=payload.get("checkpoint_id"),
                timestamp=e.timestamp,
            )
        )

    return TimelineResponse(
        task_id=task_id,
        total_events=len(timeline_events),
        stages_covered=sorted(list(stages_covered)),
        timeline=timeline_events,
    )


# --- Artifacts ---

@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse, summary="Get Artifact Metadata")
async def get_artifact(
    artifact_id: str,
    store: StateStore = Depends(get_state_store),
) -> ArtifactResponse:
    """Retrieve metadata and filesystem path for an engineering artifact."""
    artifact = await store.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact '{artifact_id}' not found")

    return ArtifactResponse(
        id=artifact.id,
        task_id=artifact.task_id,
        name=artifact.name,
        path=artifact.path,
        file_type=artifact.file_type,
        size_bytes=artifact.size_bytes,
        checksum=artifact.checksum,
        created_at=artifact.created_at,
    )


# --- Project Workspace Routes (Legacy Support) ---

class ProjectCreateRequest(BaseModel):
    name: str = Field(..., description="Project name", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="Project goal or context")
    config: Dict[str, Any] = Field(default_factory=dict, description="Custom project configurations")


@router.post(
    "/projects",
    response_model=ProjectWorkspace,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Isolated Project Workspace",
)
async def create_project(
    request: ProjectCreateRequest,
    settings: Settings = Depends(get_settings),
    store: StateStore = Depends(get_state_store),
) -> ProjectWorkspace:
    """Create a new isolated project workspace directory."""
    project_id = str(uuid4())
    workspace_dir = settings.base_dir / settings.workspaces_dir / project_id
    workspace_dir.mkdir(parents=True, exist_ok=True)
    (workspace_dir / "src").mkdir(exist_ok=True)
    (workspace_dir / "tests").mkdir(exist_ok=True)
    (workspace_dir / ".forge").write_text(f"project_id: {project_id}\nname: {request.name}\n", encoding="utf-8")

    project = ProjectWorkspace(
        id=project_id,
        name=request.name,
        description=request.description,
        workspace_path=str(workspace_dir.resolve()),
        config=request.config,
    )
    return await store.create_project(project)


@router.get("/projects", response_model=List[ProjectWorkspace], summary="List All Projects")
async def list_projects(store: StateStore = Depends(get_state_store)) -> List[ProjectWorkspace]:
    return await store.list_projects()


@router.get("/projects/{project_id}", response_model=ProjectWorkspace, summary="Get Project by ID")
async def get_project(project_id: str, store: StateStore = Depends(get_state_store)) -> ProjectWorkspace:
    project = await store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found")
    return project

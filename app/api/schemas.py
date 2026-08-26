"""
Pydantic Request and Response Schemas for the FORGE REST API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.memory.models import TaskMode, TaskState
from app.providers.base import ProviderCapabilities, ProviderHealthStatus

# --- Task Schemas ---

class TaskCreateRequest(BaseModel):
    goal: str = Field(..., description="High-level engineering objective", min_length=3)
    requirements: list[str] = Field(default_factory=list, description="Explicit constraints or requirements")
    mode: TaskMode = Field(default=TaskMode.AUTONOMOUS, description="Execution mode")
    workspace: str | None = Field(default=None, description="Optional custom workspace path or identifier")
    repo_url: str | None = Field(default=None, description="Optional remote Git repository URL to clone")
    local_path: str | None = Field(default=None, description="Optional local directory path to copy into project sandbox")
    max_budget: float = Field(default=10.0, ge=0.1, description="Maximum allowed budget in USD")


class TaskActionRequest(BaseModel):
    reason: str | None = Field(default=None, description="Optional explanation for the action")


class TaskResponse(BaseModel):
    id: str
    goal: str
    requirements: list[str]
    mode: TaskMode
    workspace_path: str
    max_budget: float
    budget_consumed: float
    state: TaskState
    progress_percentage: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class TaskDetailResponse(TaskResponse):
    workspace_dirs: dict[str, str]
    latest_checkpoint_id: str | None = None
    checkpoints_count: int = 0


class TaskActionResponse(BaseModel):
    task_id: str
    previous_state: TaskState
    current_state: TaskState
    message: str
    checkpoint_id: str | None = None


# --- Run / Audit Event Schemas ---

class AuditEventResponse(BaseModel):
    id: str
    task_id: str
    event_type: str
    payload: dict[str, Any]
    timestamp: datetime


class RunAuditResponse(BaseModel):
    task_id: str
    total_events: int
    events: list[AuditEventResponse]


# --- Artifact Schemas ---

class ArtifactResponse(BaseModel):
    id: str
    task_id: str
    name: str
    path: str
    file_type: str
    size_bytes: int
    checksum: str | None = None
    created_at: datetime


# --- Capabilities & Diagnostic Schemas ---

class EngineCapabilitiesResponse(BaseModel):
    engine_name: str = "FORGE Autonomous Software Engineering Engine"
    version: str
    supported_modes: list[str]
    lifecycle_states: list[str]
    features: dict[str, bool]
    provider: ProviderCapabilities


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database_connected: bool
    default_provider: ProviderHealthStatus
    capabilities: ProviderCapabilities


class TimelineEvent(BaseModel):
    id: str
    task_id: str
    run_id: str
    stage: str
    agent_id: str
    provider_model: str
    action: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    duration_ms: float = 0.0
    checkpoint_id: str | None = None
    timestamp: datetime


class TimelineResponse(BaseModel):
    task_id: str
    total_events: int
    stages_covered: list[str]
    timeline: list[TimelineEvent]

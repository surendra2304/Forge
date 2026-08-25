"""
Pydantic Request and Response Schemas for the FORGE REST API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.memory.models import TaskMode, TaskState
from app.providers.base import ProviderCapabilities, ProviderHealthStatus


# --- Task Schemas ---

class TaskCreateRequest(BaseModel):
    goal: str = Field(..., description="High-level engineering objective", min_length=3)
    requirements: List[str] = Field(default_factory=list, description="Explicit constraints or requirements")
    mode: TaskMode = Field(default=TaskMode.AUTONOMOUS, description="Execution mode")
    workspace: Optional[str] = Field(default=None, description="Optional custom workspace path or identifier")
    max_budget: float = Field(default=10.0, ge=0.1, description="Maximum allowed budget in USD")


class TaskActionRequest(BaseModel):
    reason: Optional[str] = Field(default=None, description="Optional explanation for the action")


class TaskResponse(BaseModel):
    id: str
    goal: str
    requirements: List[str]
    mode: TaskMode
    workspace_path: str
    max_budget: float
    budget_consumed: float
    state: TaskState
    progress_percentage: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TaskDetailResponse(TaskResponse):
    workspace_dirs: Dict[str, str]
    latest_checkpoint_id: Optional[str] = None
    checkpoints_count: int = 0


class TaskActionResponse(BaseModel):
    task_id: str
    previous_state: TaskState
    current_state: TaskState
    message: str
    checkpoint_id: Optional[str] = None


# --- Run / Audit Event Schemas ---

class AuditEventResponse(BaseModel):
    id: str
    task_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime


class RunAuditResponse(BaseModel):
    task_id: str
    total_events: int
    events: List[AuditEventResponse]


# --- Artifact Schemas ---

class ArtifactResponse(BaseModel):
    id: str
    task_id: str
    name: str
    path: str
    file_type: str
    size_bytes: int
    checksum: Optional[str] = None
    created_at: datetime


# --- Capabilities & Diagnostic Schemas ---

class EngineCapabilitiesResponse(BaseModel):
    engine_name: str = "FORGE Autonomous Software Engineering Engine"
    version: str
    supported_modes: List[str]
    lifecycle_states: List[str]
    features: Dict[str, bool]
    provider: ProviderCapabilities


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database_connected: bool
    default_provider: ProviderHealthStatus
    capabilities: ProviderCapabilities

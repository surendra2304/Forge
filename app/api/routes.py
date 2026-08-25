"""
API Routes for Project FORGE.
Includes /health and /projects endpoints for workspace management and system diagnostics.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.memory.db import db_manager
from app.memory.models import ProjectWorkspace
from app.memory.state_store import StateStore
from app.providers.base import ProviderCapabilities, ProviderHealthStatus
from app.providers.direct import DirectProvider

logger = get_logger("api.routes")
router = APIRouter()


# --- Request & Response Models ---

class ProjectCreateRequest(BaseModel):
    name: str = Field(..., description="Project name", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="Project goal or context")
    config: Dict[str, Any] = Field(default_factory=dict, description="Custom project configurations")


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database_connected: bool
    default_provider: ProviderHealthStatus
    capabilities: ProviderCapabilities


# --- Dependencies ---

def get_state_store() -> StateStore:
    return StateStore(db_manager)


def get_default_provider(settings: Settings = Depends(get_settings)) -> DirectProvider:
    return DirectProvider(model_name=settings.default_model)


# --- Endpoints ---

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
    """
    Create a new isolated workspace directory and persist project state.
    """
    project_id = str(uuid4())
    # Create isolated directory for project inside workspaces/
    workspace_dir = settings.base_dir / settings.workspaces_dir / project_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Initialize workspace scaffold
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

    try:
        saved_project = await store.create_project(project)
        logger.info(f"Created isolated workspace for project '{request.name}' at {workspace_dir}")
        return saved_project
    except Exception as e:
        logger.error(f"Failed to persist project in database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project workspace: {str(e)}",
        )


@router.get(
    "/projects",
    response_model=List[ProjectWorkspace],
    summary="List All Projects",
)
async def list_projects(store: StateStore = Depends(get_state_store)) -> List[ProjectWorkspace]:
    """Retrieve all projects and workspaces."""
    return await store.list_projects()


@router.get(
    "/projects/{project_id}",
    response_model=ProjectWorkspace,
    summary="Get Project by ID",
)
async def get_project(
    project_id: str,
    store: StateStore = Depends(get_state_store),
) -> ProjectWorkspace:
    """Retrieve project details and workspace path by ID."""
    project = await store.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )
    return project

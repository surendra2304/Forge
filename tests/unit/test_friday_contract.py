"""
Unit tests for FRIDAY <-> FORGE Integration Contract and ID Propagation.
"""

from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.schemas import FORGETaskResult, FRIDAYTaskRequest
from app.core.config import Settings
from app.core.orchestrator import OrchestratorCore
from app.core.workspace import WorkspaceManager
from app.execution.engine import ExecutionEngine
from app.main import app
from app.memory.db import DatabaseManager
from app.memory.state_store import StateStore


@pytest.mark.asyncio
async def test_friday_delegation_and_id_propagation(temp_dir: Path):
    """
    Validates end-to-end task delegation from FRIDAY:
    FRIDAYTaskRequest -> Task Intake & Wave Execution -> Delivery Packaging -> FORGETaskResult.
    """
    db_mgr = DatabaseManager(db_path=temp_dir / "friday_contract.db")
    await db_mgr.init_db()
    store = StateStore(db_mgr)

    settings = Settings()
    settings.workspaces_dir = temp_dir / "workspaces"
    wm = WorkspaceManager(settings=settings)
    engine = ExecutionEngine(wm=wm)
    orchestrator = OrchestratorCore(store=store, wm=wm, engine=engine)

    from app.api.routes import get_orchestrator, get_state_store, get_workspace_manager
    app.dependency_overrides[get_state_store] = lambda: store
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_workspace_manager] = lambda: wm

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Delegate Task from FRIDAY
        req_payload = {
            "friday_task_id": "friday-task-uuid-8888",
            "goal": "Build micro service for FRIDAY assistant",
            "requirements": ["FastAPI endpoint", "Unit tests", "Zero external host side-effects"],
            "permission_scope": "sandbox",
            "user_authorized": True,
            "acceptance_criteria": ["All tests pass", "Lint clean"],
            "mode": "autonomous",
        }

        resp = await client.post("/friday/delegate", json=req_payload)
        assert resp.status_code == 200

        data = resp.json()
        assert data["friday_task_id"] == "friday-task-uuid-8888"
        assert data["forge_task_id"] is not None
        assert data["forge_run_id"] == f"run_{data['forge_task_id'][:8]}"
        assert data["status"].lower() in ["completed", "ready", "running"]
        assert "artifacts" in data["artifact_location"]
        assert "implementation_summary" in data
        assert "tests_build_evidence" in data
        assert len(data["follow_up_suggestions"]) >= 1

        forge_tid = data["forge_task_id"]

        # 2. Fetch Result via GET endpoint
        res_get = await client.get(f"/friday/tasks/{forge_tid}/result")
        assert res_get.status_code == 200
        get_data = res_get.json()
        assert get_data["forge_task_id"] == forge_tid
        assert get_data["status"] == data["status"]

    app.dependency_overrides.clear()

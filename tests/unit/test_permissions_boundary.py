"""
Unit tests for FORGE Permission Boundary and API Key Authentication.
"""

from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.orchestrator import OrchestratorCore
from app.core.workspace import WorkspaceManager
from app.execution.engine import ExecutionEngine
from app.main import app
from app.memory.db import DatabaseManager
from app.memory.state_store import StateStore


@pytest.mark.asyncio
async def test_permission_boundary_blocks_unauthorized_scope(temp_dir: Path):
    """
    Validates that requests with restricted scopes ('unrestricted', 'production_deploy')
    without explicit user authorization are rejected with HTTP 403 Forbidden.
    """
    db_mgr = DatabaseManager(db_path=temp_dir / "perm_boundary.db")
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
        # 1. Unrestricted scope without authorization -> 403
        bad_req = {
            "friday_task_id": "bad-task-001",
            "goal": "Modify root filesystem",
            "permission_scope": "unrestricted",
            "user_authorized": False,
        }
        res_403 = await client.post("/friday/delegate", json=bad_req)
        assert res_403.status_code == 403
        assert "exceeds autonomous workspace sandbox" in res_403.json()["detail"]

        # 2. Production deploy without authorization -> 403
        deploy_req = {
            "friday_task_id": "bad-task-002",
            "goal": "Deploy directly to production clusters",
            "permission_scope": "production_deploy",
            "user_authorized": False,
        }
        res_deploy_403 = await client.post("/friday/delegate", json=deploy_req)
        assert res_deploy_403.status_code == 403

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_key_authentication_enforcement(temp_dir: Path, monkeypatch):
    """
    Validates API key authentication:
    - 401 when invalid or missing key.
    - 200 with X-API-Key or Bearer token.
    """
    db_mgr = DatabaseManager(db_path=temp_dir / "auth_test.db")
    await db_mgr.init_db()
    store = StateStore(db_mgr)

    settings = Settings(api_key="forge_secret_master_key_12345")
    settings.workspaces_dir = temp_dir / "workspaces"
    wm = WorkspaceManager(settings=settings)
    engine = ExecutionEngine(wm=wm)
    orchestrator = OrchestratorCore(store=store, wm=wm, engine=engine)

    from app.core.config import get_settings
    from app.api.routes import get_orchestrator, get_state_store, get_workspace_manager
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_state_store] = lambda: store
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_workspace_manager] = lambda: wm

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        req_payload = {
            "friday_task_id": "auth-task-001",
            "goal": "Authenticated task delegation",
            "permission_scope": "sandbox",
            "user_authorized": True,
        }

        # 1. Missing API Key -> 401
        res_no_auth = await client.post("/friday/delegate", json=req_payload)
        assert res_no_auth.status_code == 401

        # 2. Invalid API Key -> 401
        res_bad_auth = await client.post(
            "/friday/delegate",
            json=req_payload,
            headers={"X-API-Key": "wrong_key"},
        )
        assert res_bad_auth.status_code == 401

        # 3. Valid X-API-Key -> 200
        res_x_key = await client.post(
            "/friday/delegate",
            json=req_payload,
            headers={"X-API-Key": "forge_secret_master_key_12345"},
        )
        assert res_x_key.status_code == 200

        # 4. Valid Bearer Token -> 200
        res_bearer = await client.post(
            "/friday/delegate",
            json=req_payload,
            headers={"Authorization": "Bearer forge_secret_master_key_12345"},
        )
        assert res_bearer.status_code == 200

    app.dependency_overrides.clear()

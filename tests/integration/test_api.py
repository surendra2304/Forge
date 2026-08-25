"""
Integration tests for FastAPI endpoints: /health and /projects.
"""

from pathlib import Path
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database_connected"] is True
    assert "version" in data
    assert "default_provider" in data
    assert data["default_provider"]["healthy"] is True
    assert "capabilities" in data
    assert data["capabilities"]["provider_name"] == "DirectProvider"


@pytest.mark.asyncio
async def test_create_project_and_workspace(async_client: AsyncClient):
    payload = {
        "name": "Integration Test Engine",
        "description": "Verify automated workspace provisioning and persistence",
        "config": {"language": "python", "timeout_seconds": 300},
    }

    response = await async_client.post("/projects", json=payload)
    assert response.status_code == 201

    project_data = response.json()
    assert "id" in project_data
    assert project_data["name"] == payload["name"]
    assert project_data["description"] == payload["description"]
    assert project_data["config"]["language"] == "python"

    workspace_path = Path(project_data["workspace_path"])
    assert workspace_path.exists()
    assert (workspace_path / "src").exists()
    assert (workspace_path / "tests").exists()
    assert (workspace_path / ".forge").exists()

    # Verify retrieval via GET /projects/{id}
    get_res = await async_client.get(f"/projects/{project_data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_data["id"]

    # Verify listing via GET /projects
    list_res = await async_client.get("/projects")
    assert list_res.status_code == 200
    all_projects = list_res.json()
    assert any(p["id"] == project_data["id"] for p in all_projects)


@pytest.mark.asyncio
async def test_get_nonexistent_project(async_client: AsyncClient):
    response = await async_client.get("/projects/non-existent-uuid-1234")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

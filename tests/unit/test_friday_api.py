"""
Integration tests for FRIDAY Task Management API endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.memory.db import db_manager
from app.memory.state_store import StateStore


@pytest.mark.asyncio
async def test_friday_task_lifecycle_api():
    await db_manager.init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Submit task with FRIDAY metadata
        payload = {
            "goal": "Build a responsive landing page for FRIDAY",
            "requirements": ["Responsive layout", "Hero banner"],
            "max_budget": 5.0,
            "task_metadata": {
                "source": "friday",
                "priority": "high",
                "tags": ["frontend", "landing-page"],
            },
        }
        res = await client.post("/api/tasks", json=payload)
        assert res.status_code == 201
        data = res.json()
        task_id = data["id"]
        assert data["goal"] == payload["goal"]
        assert data["metadata"]["source"] == "friday"
        assert data["metadata"]["priority"] == "high"

        # 2. List tasks
        res_list = await client.get("/api/tasks")
        assert res_list.status_code == 200
        summaries = res_list.json()
        assert len(summaries) >= 1
        assert any(s["id"] == task_id for s in summaries)

        # 3. Get detailed task status and ETA
        res_get = await client.get(f"/api/tasks/{task_id}")
        assert res_get.status_code == 200
        detail = res_get.json()
        assert detail["id"] == task_id
        assert "estimated_remaining_seconds" in detail
        assert "workspace_dirs" in detail

        # 4. Deep Inspection
        res_inspect = await client.get(f"/api/tasks/{task_id}/inspect")
        assert res_inspect.status_code == 200
        inspect_data = res_inspect.json()
        assert inspect_data["task_id"] == task_id
        assert "files_created" in inspect_data
        assert "dependencies" in inspect_data
        assert "verification_summary" in inspect_data

        # 5. Logs endpoint
        res_logs = await client.get(f"/api/tasks/{task_id}/logs")
        assert res_logs.status_code == 200
        logs_data = res_logs.json()
        assert "logs" in logs_data

        # 6. Artifacts endpoint
        res_art = await client.get(f"/api/tasks/{task_id}/artifacts")
        assert res_art.status_code == 200
        assert isinstance(res_art.json(), list)

        # 7. Cancel endpoint
        res_cancel = await client.post(f"/api/tasks/{task_id}/cancel", json={"reason": "User requested abort"})
        assert res_cancel.status_code == 200
        assert res_cancel.json()["current_state"] == "CANCELLED"

        # 8. Archive (soft delete) endpoint
        res_archive = await client.delete(f"/api/tasks/{task_id}")
        assert res_archive.status_code == 200
        assert res_archive.json()["archived"] is True

        # Confirm excluded from standard listing
        res_list_after = await client.get("/api/tasks")
        assert not any(s["id"] == task_id for s in res_list_after.json())

        # Confirm present when include_archived=true
        res_list_archived = await client.get("/api/tasks?include_archived=true")
        assert any(s["id"] == task_id for s in res_list_archived.json())

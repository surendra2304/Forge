"""
Unit tests for FRIDAY Task Source and Webhook Integration.
"""

from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient, Response
import pytest
from app.integrations.friday_source import (
    FridaySourceManager,
    FridayTaskContext,
    friday_source_manager,
)
from app.main import app
from app.memory.db import db_manager
from app.memory.models import TaskEntity, TaskState
from app.memory.state_store import StateStore


def test_friday_source_detection_and_logging():
    mgr = FridaySourceManager(base_url="http://localhost:9000")
    meta_friday = {"source": "friday", "priority": "urgent"}
    assert mgr.is_friday_task(meta_friday) is True

    meta_other = {"source": "cli"}
    assert mgr.is_friday_task(meta_other) is False

    log_msg = mgr.format_log_message("task_123", "Synthesizing frontend assets")
    assert "[FRIDAY-TASK: task_123]" in log_msg


@pytest.mark.asyncio
async def test_friday_webhook_notification_success():
    mgr = FridaySourceManager(base_url="http://mock-friday:9000", api_key="secret")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = Response(200, json={"status": "received"})
        delivered = await mgr.notify_event(
            task_id="task_999",
            event_type="stage_completed",
            data={"stage": "Architecture", "progress": 30},
        )
        assert delivered is True
        assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_friday_webhook_notification_failure_graceful():
    mgr = FridaySourceManager(base_url="http://invalid-friday-host:9000")

    with patch("httpx.AsyncClient.post", side_effect=RuntimeError("Connection refused")):
        delivered = await mgr.notify_event(
            task_id="task_fail",
            event_type="task_failed",
            data={"error": "Build error"},
            max_retries=2,
        )
        assert delivered is False  # Fails gracefully without raising uncaught exception


@pytest.mark.asyncio
async def test_friday_context_api():
    await db_manager.init_db()
    store = StateStore(db_manager)

    task = TaskEntity(
        id="task_ctx_01",
        goal="Build trading dashboard",
        workspace_path="workspaces/task_ctx_01",
        state=TaskState.RUNNING,
        metadata={
            "source": "friday",
            "priority": "high",
            "tags": ["finance", "dashboard"],
            "correlation_id": "friday_cmd_42",
        },
    )
    await store.save_task(task)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/api/tasks/{task.id}/friday-context")
        assert res.status_code == 200
        data = res.json()
        assert data["task_id"] == task.id
        assert data["source"] == "friday"
        assert data["priority"] == "high"
        assert data["correlation_id"] == "friday_cmd_42"
        assert data["tags"] == ["finance", "dashboard"]

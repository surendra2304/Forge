"""
Unit tests for Generic Consumer-Agnostic Webhook Dispatcher.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.api.webhooks import webhook_dispatcher
from app.main import app
from app.memory.db import db_manager


@pytest.mark.asyncio
async def test_webhook_dispatch_success():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = Response(200, json={"status": "ok"})

        delivered = await webhook_dispatcher.dispatch_event(
            webhook_url="https://example.com/webhook",
            task_id="task_webhook_1",
            event="stage_completed",
            data={"stage": "Architecture", "progress": 35},
        )
        assert delivered is True
        assert mock_post.call_count == 1
        _, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        assert payload["event"] == "stage_completed"
        assert payload["task_id"] == "task_webhook_1"
        assert payload["source"] == "forge"


@pytest.mark.asyncio
async def test_webhook_dispatch_no_url():
    # If no URL is provided, returns False cleanly
    delivered = await webhook_dispatcher.dispatch_event(
        webhook_url=None,
        task_id="task_no_hook",
        event="task_started",
    )
    assert delivered is False


@pytest.mark.asyncio
async def test_webhook_dispatch_retry_and_graceful_fail():
    with patch("httpx.AsyncClient.post", side_effect=RuntimeError("Connection dropped")):
        delivered = await webhook_dispatcher.dispatch_event(
            webhook_url="https://unreachable.domain/webhook",
            task_id="task_fail",
            event="task_failed",
            max_retries=2,
        )
        assert delivered is False


@pytest.mark.asyncio
async def test_task_creation_with_webhook_url():
    await db_manager.init_db()

    with patch.object(
        webhook_dispatcher, "dispatch_event", new_callable=AsyncMock
    ) as mock_dispatch:
        mock_dispatch.return_value = True

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/tasks",
                json={
                    "goal": "Build a static portfolio website",
                    "webhook_url": "https://callback.service/events",
                },
            )
            assert res.status_code == 201
            data = res.json()
            assert data["metadata"]["webhook_url"] == "https://callback.service/events"
            assert mock_dispatch.called

"""Unit tests for bounded and SSRF-aware webhook delivery."""

import asyncio
import socket
from unittest.mock import AsyncMock, call, patch

import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.api import webhooks as webhooks_module
from app.api.webhooks import (
    _is_public_address,
    _resolve_public_webhook_target,
    _retry_after_seconds,
    webhook_dispatcher,
)
from app.main import app
from app.memory.db import DatabaseManager


@pytest.fixture
def public_webhook_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep delivery tests deterministic without depending on a public DNS resolver."""
    monkeypatch.setattr(
        webhooks_module,
        "_resolve_public_webhook_target",
        AsyncMock(return_value=True),
    )


@pytest.mark.asyncio
async def test_webhook_dispatch_success_for_any_2xx_response(
    public_webhook_resolution: None,
) -> None:
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = Response(206, json={"status": "accepted"})
        delivered = await webhook_dispatcher.dispatch_event(
            webhook_url="https://example.com/webhook",
            task_id="task_webhook_1",
            event="stage_completed",
            data={"stage": "Architecture", "progress": 35},
        )

    assert delivered
    assert mock_post.await_count == 1
    _, kwargs = mock_post.call_args
    payload = kwargs.get("json", {})
    assert payload["event"] == "stage_completed"
    assert payload["task_id"] == "task_webhook_1"
    assert payload["source"] == "forge"


@pytest.mark.asyncio
async def test_webhook_dispatch_no_url() -> None:
    delivered = await webhook_dispatcher.dispatch_event(
        webhook_url=None,
        task_id="task_no_hook",
        event="task_started",
    )
    assert delivered is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "https:///missing-host",
        "https://user:secret@example.com/webhook",
        "https://example.com:not-a-port/webhook",
        "http://127.0.0.1/private",
        "http://169.254.169.254/latest/meta-data/",
    ],
)
async def test_webhook_rejects_invalid_or_private_urls_without_network_calls(url: str) -> None:
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        delivered = await webhook_dispatcher.dispatch_event(
            webhook_url=url,
            task_id="task_invalid_url",
            event="task_started",
        )

    assert not delivered
    mock_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_webhook_retries_transport_errors_and_fails_gracefully(
    public_webhook_resolution: None,
) -> None:
    with (
        patch(
            "httpx.AsyncClient.post",
            new_callable=AsyncMock,
            side_effect=RuntimeError("simulated transport failure"),
        ) as mock_post,
        patch("app.api.webhooks.asyncio.sleep", new_callable=AsyncMock) as sleep,
        patch("app.api.webhooks.random.uniform", return_value=0.0),
    ):
        delivered = await webhook_dispatcher.dispatch_event(
            webhook_url="https://unreachable.domain/webhook",
            task_id="task_fail",
            event="task_failed",
            max_retries=3,
        )

    assert delivered is False
    assert mock_post.await_count == 3
    assert sleep.await_args_list == [call(0.2), call(0.4)]


@pytest.mark.asyncio
async def test_webhook_retries_transient_statuses_and_honors_retry_after(
    public_webhook_resolution: None,
) -> None:
    with (
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        patch("app.api.webhooks.asyncio.sleep", new_callable=AsyncMock) as sleep,
        patch("app.api.webhooks.random.uniform", return_value=0.0),
    ):
        mock_post.side_effect = [
            Response(503),
            Response(429, headers={"Retry-After": "1.25"}),
            Response(204),
        ]
        delivered = await webhook_dispatcher.dispatch_event(
            webhook_url="https://receiver.example/events",
            task_id="task_transient",
            event="task_completed",
            max_retries=3,
        )

    assert delivered
    assert mock_post.await_count == 3
    assert sleep.await_args_list == [call(0.2), call(1.25)]


@pytest.mark.asyncio
async def test_permanent_client_error_fails_fast_without_retry(
    public_webhook_resolution: None,
) -> None:
    with (
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        patch("app.api.webhooks.asyncio.sleep", new_callable=AsyncMock) as sleep,
    ):
        mock_post.return_value = Response(400, text="invalid payload")
        delivered = await webhook_dispatcher.dispatch_event(
            webhook_url="https://receiver.example/events",
            task_id="task_bad_request",
            event="task_completed",
            max_retries=3,
        )

    assert not delivered
    mock_post.assert_awaited_once()
    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancellation_propagates_without_retrying(
    public_webhook_resolution: None,
) -> None:
    with (
        patch(
            "httpx.AsyncClient.post",
            new_callable=AsyncMock,
            side_effect=asyncio.CancelledError,
        ) as mock_post,
        patch("app.api.webhooks.asyncio.sleep", new_callable=AsyncMock) as sleep,
    ):
        with pytest.raises(asyncio.CancelledError):
            await webhook_dispatcher.dispatch_event(
                webhook_url="https://receiver.example/events",
                task_id="task_cancel",
                event="task_completed",
                max_retries=3,
            )

    mock_post.assert_awaited_once()
    sleep.assert_not_awaited()


@pytest.mark.parametrize("attempts", [0, -1, 1.5, True, 9])
@pytest.mark.asyncio
async def test_webhook_rejects_invalid_attempt_limits(attempts) -> None:
    with pytest.raises(ValueError, match="max_retries"):
        await webhook_dispatcher.dispatch_event(
            webhook_url="https://receiver.example/events",
            task_id="task_bad_attempts",
            event="task_completed",
            max_retries=attempts,
        )


def test_public_address_classifier_rejects_local_and_special_ranges() -> None:
    for address in (
        "127.0.0.1",
        "10.1.2.3",
        "172.16.0.1",
        "192.168.1.2",
        "169.254.169.254",
        "100.64.0.1",
        "::1",
        "fc00::1",
        "fe80::1",
        "ff02::1",
        "0.0.0.0",
        "not-an-ip",
    ):
        assert not _is_public_address(address), address
    assert _is_public_address("8.8.8.8")
    assert _is_public_address("2606:4700:4700::1111")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("host", "port"),
    [
        ("localhost", 80),
        ("service.local", 8080),
        ("127.0.0.1", 443),
        ("169.254.169.254", 80),
        ("::1", 443),
        ("fc00::1", 443),
    ],
)
async def test_resolver_rejects_private_literal_and_local_hosts(host: str, port: int) -> None:
    assert not await _resolve_public_webhook_target(host, port)


@pytest.mark.asyncio
async def test_resolver_rejects_mixed_public_and_private_dns_answers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    public_record = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
    private_record = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.8", 443))
    monkeypatch.setattr(
        webhooks_module,
        "_lookup_webhook_addresses",
        AsyncMock(return_value=[public_record, private_record]),
    )

    assert not await _resolve_public_webhook_target("mixed.example", 443)


@pytest.mark.asyncio
async def test_resolver_accepts_only_public_dns_answers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
    ]
    monkeypatch.setattr(
        webhooks_module,
        "_lookup_webhook_addresses",
        AsyncMock(return_value=records),
    )

    assert await _resolve_public_webhook_target("public.example", 443)


@pytest.mark.asyncio
async def test_dns_failure_rejects_webhook_without_posting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        webhooks_module,
        "_lookup_webhook_addresses",
        AsyncMock(side_effect=OSError("resolver unavailable")),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        delivered = await webhook_dispatcher.dispatch_event(
            webhook_url="https://does-not-resolve.example/events",
            task_id="task_dns_failure",
            event="task_started",
        )

    assert not delivered
    mock_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_retry_after_parser_handles_seconds_and_bounds_waits() -> None:
    assert _retry_after_seconds("1.5") == 1.5
    assert _retry_after_seconds("100000") == 10.0
    assert _retry_after_seconds("-1") is None
    assert _retry_after_seconds("not-a-date") is None


@pytest.mark.asyncio
async def test_task_creation_with_webhook_url(isolated_db_manager: DatabaseManager) -> None:
    # Use the isolated test database rather than the process-global data/forge.db.
    await isolated_db_manager.init_db()

    with patch.object(
        webhook_dispatcher, "dispatch_event", new_callable=AsyncMock
    ) as mock_dispatch:
        mock_dispatch.return_value = True
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/tasks",
                json={
                    "goal": "Build a static portfolio website",
                    "webhook_url": "https://callback.service/events",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["metadata"]["webhook_url"] == "https://callback.service/events"
    assert mock_dispatch.called

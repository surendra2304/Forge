from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Response

from app.api import tasks as tasks_module
from app.api.schemas import TaskCreateRequest, TaskResponse
from app.memory.db import DatabaseManager
from app.memory.models import TaskEntity, TaskMode, TaskState
from app.memory.state_store import StateStore


class FakeOrchestrator:
    def __init__(self, store: StateStore, workspace_path: str):
        self.store = store
        self.workspace_path = workspace_path
        self.calls: list[dict[str, Any]] = []

    async def intake_and_plan(self, **kwargs):
        self.calls.append(dict(kwargs))
        if getattr(self, "failure", False):
            raise RuntimeError("synthetic intake failure")
        task_id = kwargs.get("task_id_override", f"task_direct_{len(self.calls)}")
        task = TaskEntity(
            id=task_id,
            goal=kwargs["goal"],
            requirements=kwargs["requirements"] or [],
            mode=kwargs["mode"],
            workspace_path=self.workspace_path,
            max_budget=kwargs["max_budget"],
            state=TaskState.READY,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await self.store.create_task(task)
        return task, None


@pytest.fixture
def quiet_task_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tasks_module, "_schedule_execution", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        tasks_module.ws_manager, "broadcast_global", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(
        tasks_module.webhook_dispatcher, "dispatch_event", AsyncMock(return_value=True)
    )
    monkeypatch.setattr(
        tasks_module.ProgressTracker, "get_or_create", lambda *args, **kwargs: object()
    )


def make_request(goal: str = "Build a responsive dashboard") -> TaskCreateRequest:
    return TaskCreateRequest(goal=goal, max_budget=2.0, mode=TaskMode.PLAN_ONLY)


async def submit(
    request: TaskCreateRequest,
    orchestrator: FakeOrchestrator,
    store: StateStore,
    *,
    key: str | None = None,
) -> tuple[TaskResponse, Response]:
    response = Response(status_code=201)
    result = await tasks_module.create_task(
        request=request,
        response=response,
        idempotency_key=key,
        orchestrator=orchestrator,  # type: ignore[arg-type]
        store=store,
    )
    return result, response


@pytest.mark.asyncio
async def test_idempotency_records_are_persisted_across_store_instances(
    test_db_manager: DatabaseManager,
) -> None:
    await test_db_manager.init_db()
    first_store = StateStore(test_db_manager)
    second_store = StateStore(test_db_manager)

    first = await first_store.claim_idempotency_key(
        "key-digest", "request-fingerprint", "task_reserved", "owner-one"
    )
    duplicate = await second_store.claim_idempotency_key(
        "key-digest", "request-fingerprint", "task-other", "owner-two"
    )

    assert first["owned"]
    assert duplicate["owned"] is False
    assert duplicate["task_id"] == "task_reserved"
    assert duplicate["request_fingerprint"] == "request-fingerprint"
    assert duplicate["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_concurrent_idempotency_claims_have_one_owner(
    test_db_manager: DatabaseManager,
) -> None:
    await test_db_manager.init_db()
    store = StateStore(test_db_manager)

    results = await asyncio.gather(
        *(
            store.claim_idempotency_key(
                "same-digest",
                "same-fingerprint",
                f"task-{index}",
                f"owner-{index}",
            )
            for index in range(8)
        )
    )

    assert sum(bool(result["owned"]) for result in results) == 1
    assert len({result["task_id"] for result in results}) == 1


@pytest.mark.asyncio
async def test_same_key_returns_same_task_without_rescheduling(
    test_db_manager: DatabaseManager,
    tmp_path,
    quiet_task_side_effects: None,
) -> None:
    await test_db_manager.init_db()
    store = StateStore(test_db_manager)
    orchestrator = FakeOrchestrator(store, str(tmp_path))
    request = make_request()

    first, first_response = await submit(request, orchestrator, store, key="client-request-1")
    duplicate, duplicate_response = await submit(
        make_request(), orchestrator, store, key="client-request-1"
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 200
    assert duplicate.id == first.id
    assert duplicate.state == first.state
    assert len(orchestrator.calls) == 1
    assert "task_id_override" in orchestrator.calls[0]


@pytest.mark.asyncio
async def test_same_key_with_different_request_is_conflict(
    test_db_manager: DatabaseManager,
    tmp_path,
    quiet_task_side_effects: None,
) -> None:
    await test_db_manager.init_db()
    store = StateStore(test_db_manager)
    orchestrator = FakeOrchestrator(store, str(tmp_path))

    await submit(make_request(), orchestrator, store, key="client-request-2")
    with pytest.raises(HTTPException) as error:
        await submit(
            make_request("Delete all project files"),
            orchestrator,
            store,
            key="client-request-2",
        )

    assert error.value.status_code == 409
    assert len(orchestrator.calls) == 1


@pytest.mark.asyncio
async def test_duplicate_during_reservation_returns_retryable_conflict(
    test_db_manager: DatabaseManager,
    tmp_path,
    quiet_task_side_effects: None,
) -> None:
    await test_db_manager.init_db()
    store = StateStore(test_db_manager)
    request = make_request()
    key = "client-request-pending"
    digest = tasks_module._idempotency_key_digest(key)
    fingerprint = tasks_module._request_fingerprint(request)
    await store.claim_idempotency_key(
        digest, fingerprint, "reserved-task-not-created", "other-owner"
    )
    response = Response(status_code=201)

    with pytest.raises(HTTPException) as error:
        await tasks_module.create_task(
            request=request,
            response=response,
            idempotency_key=key,
            orchestrator=FakeOrchestrator(store, str(tmp_path)),  # type: ignore[arg-type]
            store=store,
        )

    assert error.value.status_code == 409
    assert response.headers["Retry-After"] == "1"


@pytest.mark.asyncio
async def test_failed_intake_releases_claim_when_no_task_was_persisted(
    test_db_manager: DatabaseManager,
    tmp_path,
    quiet_task_side_effects: None,
) -> None:
    await test_db_manager.init_db()
    store = StateStore(test_db_manager)
    request = make_request()
    failing = FakeOrchestrator(store, str(tmp_path))
    failing.failure = True

    with pytest.raises(RuntimeError, match="synthetic intake failure"):
        await submit(request, failing, store, key="retryable-failure")

    succeeding = FakeOrchestrator(store, str(tmp_path))
    result, response = await submit(
        make_request(), succeeding, store, key="retryable-failure"
    )

    assert response.status_code == 201
    assert result.id.startswith("task_idem_")
    assert len(succeeding.calls) == 1


@pytest.mark.asyncio
async def test_blank_idempotency_key_is_rejected(
    test_db_manager: DatabaseManager,
    tmp_path,
    quiet_task_side_effects: None,
) -> None:
    await test_db_manager.init_db()
    store = StateStore(test_db_manager)
    orchestrator = FakeOrchestrator(store, str(tmp_path))

    with pytest.raises(HTTPException) as error:
        await submit(make_request(), orchestrator, store, key="   ")

    assert error.value.status_code == 400
    assert not orchestrator.calls

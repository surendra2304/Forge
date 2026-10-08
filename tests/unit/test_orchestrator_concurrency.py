"""
Regression test for a severe concurrency bug found via live adversarial load
testing against a real running FORGE server (not just the test suite).

Symptom (live-reproduced, 100% repro rate with 20-30 truly concurrent
`POST /api/tasks` requests): every concurrent submission's HTTP response
reported the *same* task id and the *same* goal back to the caller, even
though each caller submitted a distinct goal.

Root cause (two compounding bugs in `OrchestratorCore.intake_and_plan`):

1. Task-id allocation was a classic check-then-act race: `count_tasks()` was
   read, a candidate id built from the count + current-second timestamp, and
   checked with `get_task()` -- all without any lock. Concurrent callers
   within the same wall-clock second could all compute the identical
   candidate id and all pass the `get_task() is None` check before any of
   them had inserted.

2. When two callers *did* collide on the same id, the retry-on-IntegrityError
   path correctly gave the loser a new, unique `task.id` and a new DB row --
   but every subsequent step in the function (`record_event`, `planner.plan`,
   `lifecycle.transition`, and the object ultimately returned to the HTTP
   layer) kept using the *original*, pre-retry `task_id` local variable. The
   result: the DB had correct, isolated rows, but the orchestration logic and
   the HTTP response were both silently bound to whichever task happened to
   win the original id, orphaning every other real submission in PENDING
   forever.

Fix: a process-wide `asyncio.Lock` (`_TASK_ID_ALLOC_LOCK`) now serializes id
allocation + workspace provisioning + the initial insert, and the local
`task_id` is explicitly resynced to `task.id` after that critical section
(including when a retry occurs), so every downstream step and the final
returned task are always bound to whatever id was *actually* persisted.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.core.orchestrator import OrchestratorCore
from app.memory.db import DatabaseManager
from app.memory.models import TaskState
from app.memory.state_store import StateStore


@pytest.mark.asyncio
async def test_concurrent_intake_never_collapses_to_one_task(tmp_path: Path):
    """N concurrent intake_and_plan() calls must produce N distinct, correctly
    attributed tasks -- never fewer, and never cross-contaminated goals."""
    db = DatabaseManager(db_path=tmp_path / "concurrency_test.db")
    store = StateStore(db)

    n = 25

    async def submit(i: int):
        # A fresh OrchestratorCore per call mirrors how FastAPI's
        # `get_orchestrator` dependency constructs one per request -- any fix
        # relying on an instance-level lock would not actually protect
        # concurrent HTTP requests.
        orch = OrchestratorCore(store=store)
        task, _graph = await orch.intake_and_plan(goal=f"Concurrency probe task number {i}")
        return i, task

    results = await asyncio.gather(*[submit(i) for i in range(1, n + 1)])

    ids = [task.id for _, task in results]
    assert len(set(ids)) == n, f"expected {n} unique task ids, got {len(set(ids))}: {ids}"

    for i, task in results:
        assert f"number {i}" in task.goal, (
            f"task returned for submission {i} has mismatched goal: {task.goal!r}"
        )
        # Every task must have actually been planned (READY), not left behind
        # in PENDING because the lifecycle transition silently operated on a
        # different task's stale id.
        assert task.state == TaskState.READY

    # Re-fetch every id from the store directly to rule out the response
    # object being correct while the persisted row is not.
    for i, task in results:
        persisted = await store.get_task(task.id)
        assert persisted is not None, f"task {task.id} (submission {i}) was never persisted"
        assert f"number {i}" in persisted.goal
        assert persisted.state == TaskState.READY

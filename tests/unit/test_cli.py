"""
Unit tests for FORGE Standalone CLI MVP.
"""

from pathlib import Path
from uuid import uuid4
import pytest
from app.cli import (
    handle_build,
    handle_cancel,
    handle_inspect,
    handle_logs,
    handle_pause,
    handle_resume,
    handle_status,
)
from app.core.config import Settings
from app.core.workspace import WorkspaceManager, workspace_manager
from app.memory.db import db_manager
from app.memory.models import TaskMode, TaskState
from app.memory.state_store import StateStore


@pytest.mark.asyncio
async def test_cli_build_and_status(temp_dir: Path):
    await db_manager.init_db()

    goal = "Create a minimal CLI todo tool"
    requirements = ["Add items", "List items"]

    # Run CLI build handler
    await handle_build(goal=goal, requirements=requirements, max_budget=10.0)

    # Verify task was created and stored
    store = StateStore(db_manager)
    tasks = await store.list_tasks(limit=1)
    assert len(tasks) >= 1
    task = tasks[0]
    assert task.goal == goal

    # Test status handler
    await handle_status(task.id)

    # Test inspect handler
    await handle_inspect(task.id)

    # Test logs handler
    await handle_logs(task.id)


@pytest.mark.asyncio
async def test_cli_pause_resume_cancel(temp_dir: Path):
    await db_manager.init_db()
    store = StateStore(db_manager)

    task_id = str(uuid4())
    from app.memory.models import TaskEntity
    task = TaskEntity(
        id=task_id,
        goal="CLI Control Flow Test",
        workspace_path=f"/workspaces/task_{task_id}",
        state=TaskState.PENDING,
    )
    await store.create_task(task)

    # Pause
    await handle_pause(task_id, reason="Manual pause")
    t_paused = await store.get_task(task_id)
    assert t_paused.state == TaskState.BLOCKED

    # Resume
    await handle_resume(task_id, reason="Manual resume")
    t_resumed = await store.get_task(task_id)
    assert t_resumed.state == TaskState.RUNNING

    # Cancel
    await handle_cancel(task_id, reason="Manual cancel")
    t_cancelled = await store.get_task(task_id)
    assert t_cancelled.state == TaskState.CANCELLED

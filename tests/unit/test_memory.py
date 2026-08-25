"""
Unit tests for SQLite StateStore, Task Graphs, and Checkpointing memory.
"""

from uuid import uuid4
import pytest
from app.memory.models import Checkpoint, ProjectWorkspace, TaskGraph, TaskNode, TaskStatus
from app.memory.state_store import StateStore


@pytest.mark.asyncio
async def test_project_workspace_persistence(state_store: StateStore):
    project_id = str(uuid4())
    project = ProjectWorkspace(
        id=project_id,
        name="Microservice Auth",
        description="Build OAuth2 authentication microservice",
        workspace_path="/tmp/workspaces/auth",
        config={"python_version": "3.11", "framework": "fastapi"},
    )

    created = await state_store.create_project(project)
    assert created.id == project_id

    fetched = await state_store.get_project(project_id)
    assert fetched is not None
    assert fetched.id == project_id
    assert fetched.name == "Microservice Auth"
    assert fetched.config["framework"] == "fastapi"

    all_projects = await state_store.list_projects()
    assert len(all_projects) >= 1
    assert any(p.id == project_id for p in all_projects)


@pytest.mark.asyncio
async def test_task_graph_persistence(state_store: StateStore):
    project_id = str(uuid4())
    project = ProjectWorkspace(
        id=project_id,
        name="Compiler Project",
        workspace_path="/tmp/workspaces/compiler",
    )
    await state_store.create_project(project)

    graph_id = str(uuid4())
    graph = TaskGraph(
        id=graph_id,
        project_id=project_id,
        goal="Create an AST parser for mathematical expressions",
    )

    node1 = TaskNode(id="node_1", title="Define Token Enums", status=TaskStatus.COMPLETED)
    node2 = TaskNode(id="node_2", title="Implement Lexer", status=TaskStatus.IN_PROGRESS)
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge("node_1", "node_2")

    saved_graph = await state_store.save_task_graph(graph)
    assert saved_graph.id == graph_id

    loaded_graph = await state_store.get_task_graph(graph_id)
    assert loaded_graph is not None
    assert loaded_graph.goal == "Create an AST parser for mathematical expressions"
    assert len(loaded_graph.nodes) == 2
    assert loaded_graph.nodes["node_1"].status == TaskStatus.COMPLETED
    assert loaded_graph.nodes["node_2"].dependencies == ["node_1"]

    latest_for_proj = await state_store.get_latest_task_graph_for_project(project_id)
    assert latest_for_proj is not None
    assert latest_for_proj.id == graph_id


@pytest.mark.asyncio
async def test_checkpoint_persistence(state_store: StateStore):
    project_id = str(uuid4())
    project = ProjectWorkspace(
        id=project_id,
        name="Checkpoint Test Project",
        workspace_path="/tmp/workspaces/checkpoint",
    )
    await state_store.create_project(project)

    cp1 = Checkpoint(
        id=str(uuid4()),
        project_id=project_id,
        step_number=1,
        state_data={"completed_files": ["token.py"], "tests_passing": True},
        description="Tokens implemented",
    )
    cp2 = Checkpoint(
        id=str(uuid4()),
        project_id=project_id,
        step_number=2,
        state_data={"completed_files": ["token.py", "lexer.py"], "tests_passing": True},
        description="Lexer implemented and tested",
    )

    await state_store.save_checkpoint(cp1)
    await state_store.save_checkpoint(cp2)

    history = await state_store.list_checkpoints(project_id)
    assert len(history) == 2
    assert history[0].step_number == 1
    assert history[1].step_number == 2

    latest_cp = await state_store.get_latest_checkpoint(project_id)
    assert latest_cp is not None
    assert latest_cp.step_number == 2
    assert "lexer.py" in latest_cp.state_data["completed_files"]

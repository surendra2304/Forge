"""
StateStore: Memory and state persistence interface for FORGE.
Handles projects, task graphs, node updates, and step-by-step checkpoints.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional

from app.memory.db import DatabaseManager, db_manager
from app.memory.models import Checkpoint, ProjectWorkspace, TaskGraph, TaskNode, TaskStatus
from app.core.logging import get_logger

logger = get_logger("memory.state_store")


class StateStore:
    """Provides high-level state persistence methods over SQLite."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or db_manager

    # --- Project Management ---

    async def create_project(self, project: ProjectWorkspace) -> ProjectWorkspace:
        """Persist a new project workspace."""
        async with self.db.connection() as conn:
            await conn.execute(
                """
                INSERT INTO projects (id, name, description, workspace_path, config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.id,
                    project.name,
                    project.description,
                    project.workspace_path,
                    json.dumps(project.config),
                    project.created_at.isoformat(),
                    project.updated_at.isoformat(),
                ),
            )
            await conn.commit()
        logger.debug(f"Saved project: {project.id} ({project.name})")
        return project

    async def get_project(self, project_id: str) -> Optional[ProjectWorkspace]:
        """Retrieve project workspace by ID."""
        async with self.db.connection() as conn:
            async with conn.execute(
                "SELECT id, name, description, workspace_path, config, created_at, updated_at FROM projects WHERE id = ?",
                (project_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return ProjectWorkspace(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    workspace_path=row["workspace_path"],
                    config=json.loads(row["config"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )

    async def list_projects(self) -> List[ProjectWorkspace]:
        """List all project workspaces."""
        async with self.db.connection() as conn:
            async with conn.execute("SELECT * FROM projects ORDER BY created_at DESC") as cursor:
                rows = await cursor.fetchall()
                return [
                    ProjectWorkspace(
                        id=row["id"],
                        name=row["name"],
                        description=row["description"],
                        workspace_path=row["workspace_path"],
                        config=json.loads(row["config"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                    for row in rows
                ]

    # --- Task Graph Persistence ---

    async def save_task_graph(self, graph: TaskGraph) -> TaskGraph:
        """Upsert a task graph."""
        graph.updated_at = datetime.now(timezone.utc)
        nodes_json = json.dumps({k: v.model_dump(mode="json") for k, v in graph.nodes.items()})
        edges_json = json.dumps([e.model_dump(mode="json") for e in graph.edges])

        async with self.db.connection() as conn:
            await conn.execute(
                """
                INSERT INTO task_graphs (id, project_id, goal, nodes, edges, status, current_node_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    goal = excluded.goal,
                    nodes = excluded.nodes,
                    edges = excluded.edges,
                    status = excluded.status,
                    current_node_id = excluded.current_node_id,
                    updated_at = excluded.updated_at
                """,
                (
                    graph.id,
                    graph.project_id,
                    graph.goal,
                    nodes_json,
                    edges_json,
                    graph.status.value,
                    graph.current_node_id,
                    graph.created_at.isoformat(),
                    graph.updated_at.isoformat(),
                ),
            )
            await conn.commit()
        return graph

    async def get_task_graph(self, graph_id: str) -> Optional[TaskGraph]:
        """Load a task graph by ID."""
        async with self.db.connection() as conn:
            async with conn.execute(
                "SELECT id, project_id, goal, nodes, edges, status, current_node_id, created_at, updated_at FROM task_graphs WHERE id = ?",
                (graph_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                raw_nodes = json.loads(row["nodes"])
                nodes = {k: TaskNode(**v) for k, v in raw_nodes.items()}
                raw_edges = json.loads(row["edges"])

                return TaskGraph(
                    id=row["id"],
                    project_id=row["project_id"],
                    goal=row["goal"],
                    nodes=nodes,
                    edges=raw_edges,
                    status=TaskStatus(row["status"]),
                    current_node_id=row["current_node_id"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )

    async def get_latest_task_graph_for_project(self, project_id: str) -> Optional[TaskGraph]:
        """Fetch the most recent task graph for a project."""
        async with self.db.connection() as conn:
            async with conn.execute(
                "SELECT id FROM task_graphs WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
                (project_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return await self.get_task_graph(row["id"])

    # --- Checkpoints ---

    async def save_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        """Persist a state checkpoint."""
        async with self.db.connection() as conn:
            await conn.execute(
                """
                INSERT INTO checkpoints (id, project_id, task_id, step_number, state_data, checksum, timestamp, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.id,
                    checkpoint.project_id,
                    checkpoint.task_id,
                    checkpoint.step_number,
                    json.dumps(checkpoint.state_data),
                    checkpoint.checksum,
                    checkpoint.timestamp.isoformat(),
                    checkpoint.description,
                ),
            )
            await conn.commit()
        logger.debug(f"Saved checkpoint {checkpoint.id} for project {checkpoint.project_id} (step {checkpoint.step_number})")
        return checkpoint

    async def list_checkpoints(self, project_id: str) -> List[Checkpoint]:
        """List checkpoints for a project ordered by step number."""
        async with self.db.connection() as conn:
            async with conn.execute(
                "SELECT * FROM checkpoints WHERE project_id = ? ORDER BY step_number ASC, timestamp ASC",
                (project_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    Checkpoint(
                        id=row["id"],
                        project_id=row["project_id"],
                        task_id=row["task_id"],
                        step_number=row["step_number"],
                        state_data=json.loads(row["state_data"]),
                        checksum=row["checksum"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        description=row["description"],
                    )
                    for row in rows
                ]

    async def get_latest_checkpoint(self, project_id: str) -> Optional[Checkpoint]:
        """Retrieve the most recent checkpoint for a project."""
        async with self.db.connection() as conn:
            async with conn.execute(
                "SELECT * FROM checkpoints WHERE project_id = ? ORDER BY step_number DESC, timestamp DESC LIMIT 1",
                (project_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return Checkpoint(
                    id=row["id"],
                    project_id=row["project_id"],
                    task_id=row["task_id"],
                    step_number=row["step_number"],
                    state_data=json.loads(row["state_data"]),
                    checksum=row["checksum"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    description=row["description"],
                )

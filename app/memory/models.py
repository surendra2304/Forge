"""
Pydantic data models for State, Memory, Task Graphs, and Checkpoints in FORGE.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"


class ProjectWorkspace(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(default=None, description="Project purpose or goal")
    workspace_path: str = Field(..., description="Absolute or relative filesystem path to isolated workspace")
    config: Dict[str, Any] = Field(default_factory=dict, description="Project specific configurations")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., description="Short task title")
    description: str = Field(default="", description="Detailed step instructions")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    dependencies: List[str] = Field(default_factory=list, description="IDs of prerequisite tasks")
    assigned_agent: Optional[str] = Field(default=None, description="Agent type or name assigned")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary task context and metadata")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Output artifacts or return data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskEdge(BaseModel):
    source: str = Field(..., description="Source TaskNode ID")
    target: str = Field(..., description="Target TaskNode ID")
    condition: Optional[str] = Field(default=None, description="Optional conditional transition expression")


class TaskGraph(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str = Field(..., description="Associated ProjectWorkspace ID")
    goal: str = Field(..., description="High-level engineering goal")
    nodes: Dict[str, TaskNode] = Field(default_factory=dict, description="Lookup of task nodes by ID")
    edges: List[TaskEdge] = Field(default_factory=list, description="Directed dependencies between nodes")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    current_node_id: Optional[str] = Field(default=None, description="Currently executing node")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def add_node(self, node: TaskNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, source_id: str, target_id: str, condition: Optional[str] = None) -> None:
        self.edges.append(TaskEdge(source=source_id, target=target_id, condition=condition))
        if target_id in self.nodes and source_id not in self.nodes[target_id].dependencies:
            self.nodes[target_id].dependencies.append(source_id)


class Checkpoint(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str = Field(..., description="Associated ProjectWorkspace ID")
    task_id: Optional[str] = Field(default=None, description="Current TaskNode ID at checkpoint")
    step_number: int = Field(default=0, description="Sequential step counter")
    state_data: Dict[str, Any] = Field(default_factory=dict, description="Serialized snapshot state")
    checksum: Optional[str] = Field(default=None, description="Integrity hash of the state")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: Optional[str] = Field(default=None, description="Human-readable milestone description")

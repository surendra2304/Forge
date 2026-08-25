"""
Hierarchical Task Tree for Project FORGE Planning Subsystem.
Represents goals decomposed across the standard 8-stage engineering pipeline:
Project -> Requirements -> Architecture -> Implementation -> Integration -> Verification -> Security -> Release.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from app.memory.models import TaskState


class PipelineStage(str, Enum):
    """The 8 canonical stages of the FORGE engineering tree."""
    PROJECT = "Project"
    REQUIREMENTS = "Requirements"
    ARCHITECTURE = "Architecture"
    IMPLEMENTATION = "Implementation"
    INTEGRATION = "Integration"
    VERIFICATION = "Verification"
    SECURITY = "Security"
    RELEASE = "Release"


class TreeNodeType(str, Enum):
    MILESTONE = "milestone"
    TASK = "task"
    VERIFICATION_GATE = "verification_gate"


class TaskTreeNode(BaseModel):
    """A node inside the hierarchical planning tree."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., description="Short node summary")
    description: str = Field(default="", description="Detailed step instructions or acceptance criteria")
    stage: PipelineStage = Field(..., description="Pipeline stage classification")
    node_type: TreeNodeType = Field(default=TreeNodeType.TASK)
    assigned_role: str = Field(default="developer", description="Specialist agent role assigned")
    dependencies: List[str] = Field(default_factory=list, description="IDs of prerequisite tree nodes")
    children: List["TaskTreeNode"] = Field(default_factory=list, description="Sub-tasks or nested items")
    status: TaskState = Field(default=TaskState.PENDING)
    verification_gate_criteria: Optional[str] = Field(default=None, description="Criteria if this is a gate")
    result_data: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HierarchicalTaskTree(BaseModel):
    """Complete 8-stage tree representation of an engineering project."""
    project_id: str
    goal: str
    root: TaskTreeNode
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_all_nodes(self) -> List[TaskTreeNode]:
        """Flatten and return all nodes in the tree."""
        nodes: List[TaskTreeNode] = []

        def traverse(node: TaskTreeNode):
            nodes.append(node)
            for child in node.children:
                traverse(child)

        traverse(self.root)
        return nodes

    def get_stage_nodes(self, stage: PipelineStage) -> List[TaskTreeNode]:
        """Return all nodes belonging to a specific pipeline stage."""
        return [n for n in self.get_all_nodes() if n.stage == stage]

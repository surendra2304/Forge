"""
Planner Engine for Project FORGE.
Synthesizes natural language requirements into the standard 8-stage hierarchical tree and durable executable DAG.
"""

from typing import List, Optional
from uuid import uuid4
from app.core.logging import get_logger
from app.memory.models import TaskGraph
from app.planning.graph import ExecutableTaskDAG
from app.planning.tree import (
    HierarchicalTaskTree,
    PipelineStage,
    TaskTreeNode,
    TreeNodeType,
)
from app.providers.base import BaseModelProvider
from app.providers.direct import DirectProvider

logger = get_logger("planning.planner")


class PlannerEngine:
    """Decomposes engineering goals into standard 8-stage trees and executable DAGs."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        self.provider = provider or DirectProvider(model_name="direct-planner")

    async def plan(
        self,
        task_id: str,
        goal: str,
        requirements: Optional[List[str]] = None,
    ) -> HierarchicalTaskTree:
        """
        Synthesize goal and requirements into the canonical 8-stage pipeline tree:
        Project -> Requirements -> Architecture -> Implementation -> Integration -> Verification -> Security -> Release.
        """
        req_list = requirements or []
        logger.info(f"Synthesizing 8-stage plan for task '{task_id}': {goal[:80]}...")

        # 1. Project Root
        root = TaskTreeNode(
            id=str(uuid4()),
            title=f"Project: {goal}",
            description=f"Autonomous execution of: {goal}",
            stage=PipelineStage.PROJECT,
            node_type=TreeNodeType.MILESTONE,
            assigned_role="planner",
        )

        # 2. Stage: Requirements
        node_req = TaskTreeNode(
            id=str(uuid4()),
            title="Requirements Specification & Scope Definition",
            description=f"Formalize scope and constraints: {req_list}",
            stage=PipelineStage.REQUIREMENTS,
            node_type=TreeNodeType.TASK,
            assigned_role="planner",
            dependencies=[],
        )

        # 3. Stage: Architecture
        node_arch = TaskTreeNode(
            id=str(uuid4()),
            title="System Architecture & Module Design",
            description="Formulate module boundaries, API signatures, and data models.",
            stage=PipelineStage.ARCHITECTURE,
            node_type=TreeNodeType.TASK,
            assigned_role="architect",
            dependencies=[node_req.id],
        )

        # 4. Stage: Implementation
        node_impl_core = TaskTreeNode(
            id=str(uuid4()),
            title="Core Implementation & Logic Synthesis",
            description="Author clean, idiomatic implementation conforming to architecture specification.",
            stage=PipelineStage.IMPLEMENTATION,
            node_type=TreeNodeType.TASK,
            assigned_role="developer",
            dependencies=[node_arch.id],
        )

        # 5. Stage: Integration
        node_integration = TaskTreeNode(
            id=str(uuid4()),
            title="Module Integration & Configuration Wiring",
            description="Connect components, environment variables, and dependencies.",
            stage=PipelineStage.INTEGRATION,
            node_type=TreeNodeType.TASK,
            assigned_role="developer",
            dependencies=[node_impl_core.id],
        )

        # 6. Stage: Verification
        node_verify = TaskTreeNode(
            id=str(uuid4()),
            title="Automated Test Suite & Verification Gate",
            description="Execute automated test runner to ensure 100% assertions pass.",
            stage=PipelineStage.VERIFICATION,
            node_type=TreeNodeType.VERIFICATION_GATE,
            assigned_role="tester",
            dependencies=[node_integration.id],
            verification_gate_criteria="All automated tests pass with 0 errors.",
        )

        # 7. Stage: Security
        node_sec = TaskTreeNode(
            id=str(uuid4()),
            title="Security Audit & Code Review Gate",
            description="Scan source code for vulnerabilities, secret leaks, and architectural compliance.",
            stage=PipelineStage.SECURITY,
            node_type=TreeNodeType.VERIFICATION_GATE,
            assigned_role="security_reviewer",
            dependencies=[node_verify.id],
            verification_gate_criteria="Zero secret leaks and clean security review.",
        )

        # 8. Stage: Release
        node_release = TaskTreeNode(
            id=str(uuid4()),
            title="Release Packaging & Checkpoint Tagging",
            description="Package verified artifacts, generate summary documentation, and create git release checkpoint.",
            stage=PipelineStage.RELEASE,
            node_type=TreeNodeType.MILESTONE,
            assigned_role="release_engineer",
            dependencies=[node_sec.id],
        )

        root.children = [
            node_req,
            node_arch,
            node_impl_core,
            node_integration,
            node_verify,
            node_sec,
            node_release,
        ]

        tree = HierarchicalTaskTree(
            project_id=task_id,
            goal=goal,
            root=root,
        )

        return tree

    async def create_executable_dag(
        self,
        task_id: str,
        goal: str,
        requirements: Optional[List[str]] = None,
    ) -> ExecutableTaskDAG:
        """Helper to create tree and immediately return the executable DAG."""
        tree = await self.plan(task_id, goal, requirements)
        return ExecutableTaskDAG.from_tree(tree)


planner_engine = PlannerEngine()

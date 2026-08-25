"""
Orchestrator Core for Project FORGE.
Owns the end-to-end task lifecycle, coordinating Task Analyzer, Planner, Agent Registry, and Execution Engine.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.agents.registry import AgentRegistry, agent_registry
from app.core.analyzer import TaskAnalysisResult, TaskAnalyzer, task_analyzer
from app.core.logging import get_logger
from app.core.workspace import WorkspaceManager, workspace_manager
from app.execution.engine import ExecutionEngine, execution_engine
from app.memory.db import db_manager
from app.memory.models import (
    Checkpoint,
    TaskEntity,
    TaskGraph,
    TaskMode,
    TaskState,
)
from app.memory.state_store import StateStore
from app.memory.task_lifecycle import TaskStateMachine
from app.planning.graph import ExecutableTaskDAG
from app.planning.planner import PlannerEngine, planner_engine

logger = get_logger("core.orchestrator")


class OrchestratorCore:
    """
    Central conductor of FORGE.
    Orchestrates: Request Intake -> Task Analyzer -> Planner -> State Machine -> Agent Dispatch -> Verification.
    """

    def __init__(
        self,
        store: Optional[StateStore] = None,
        wm: Optional[WorkspaceManager] = None,
        analyzer: Optional[TaskAnalyzer] = None,
        planner: Optional[PlannerEngine] = None,
        registry: Optional[AgentRegistry] = None,
        engine: Optional[ExecutionEngine] = None,
    ):
        self.store = store or StateStore(db_manager)
        self.wm = wm or workspace_manager
        self.analyzer = analyzer or task_analyzer
        self.planner = planner or planner_engine
        self.registry = registry or agent_registry
        self.engine = engine or execution_engine
        self.lifecycle = TaskStateMachine(self.store)

    async def intake_and_plan(
        self,
        goal: str,
        requirements: Optional[List[str]] = None,
        mode: TaskMode = TaskMode.AUTONOMOUS,
        max_budget: float = 10.0,
        custom_workspace: Optional[str] = None,
    ) -> tuple[TaskEntity, TaskGraph]:
        """
        Intake a user request, create isolated workspace, run Task Analyzer,
        synthesize 8-stage TaskGraph DAG, and transition task to READY.
        """
        task_id = str(uuid4())
        req_list = requirements or []
        logger.info(f"Orchestrator intaking task '{task_id}': {goal[:80]}...")

        # 1. Provision isolated workspace under workspaces/task_<id>/
        custom_base = Path(custom_workspace) if custom_workspace else None
        ws_paths = self.wm.create_workspace(task_id, custom_base=custom_base)

        # 2. Persist initial task in PENDING state
        task = TaskEntity(
            id=task_id,
            goal=goal,
            requirements=req_list,
            mode=mode,
            workspace_path=str(ws_paths.root.resolve()),
            max_budget=max_budget,
            state=TaskState.PENDING,
            progress_percentage=0,
        )
        await self.store.create_task(task)
        await self.store.record_event(
            task_id=task_id,
            event_type="task.created",
            payload={"goal": goal, "mode": mode.value, "max_budget": max_budget},
        )

        # 3. Call Task Analyzer
        analysis = await self.analyzer.analyze(goal, req_list)
        await self.store.record_event(
            task_id=task_id,
            event_type="task.analyzed",
            payload=analysis.model_dump(mode="json"),
        )

        # 4. Route to Planner: Synthesize 8-stage tree and executable DAG
        tree = await self.planner.plan(task_id, goal, req_list)
        dag = ExecutableTaskDAG.from_tree(tree)
        saved_graph = await self.store.save_task_graph(dag.graph)

        await self.store.record_event(
            task_id=task_id,
            event_type="plan.created",
            payload={
                "nodes_count": len(saved_graph.nodes),
                "edges_count": len(saved_graph.edges),
                "goal": goal,
            },
        )

        # 5. Transition task state from PENDING to READY
        ready_task = await self.lifecycle.transition(
            task_id=task_id,
            to_state=TaskState.READY,
            reason="Analysis and 8-stage DAG planning complete",
        )

        return ready_task, saved_graph

    async def step_task(self, task_id: str) -> tuple[TaskEntity, List[str]]:
        """
        Execute the next available batch of ready nodes in the DAG.
        """
        task = await self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")

        if task.state in [TaskState.COMPLETED, TaskState.CANCELLED, TaskState.BLOCKED]:
            return task, []

        # Ensure task is marked RUNNING
        if task.state != TaskState.RUNNING:
            task = await self.lifecycle.transition(task_id, TaskState.RUNNING, reason="Executing ready DAG wave")

        graph = await self.store.get_latest_task_graph_for_project(task_id)
        if not graph:
            raise ValueError(f"Task graph for task '{task_id}' not found")

        dag = ExecutableTaskDAG(graph)
        ready_nodes = dag.get_ready_nodes()
        executed_nodes: List[str] = []

        if not ready_nodes:
            if dag.is_completed():
                task = await self.lifecycle.transition(task_id, TaskState.COMPLETED, progress_percentage=100)
                await self.store.record_event(task_id=task_id, event_type="task.completed")
            return task, []

        # Execute all ready nodes concurrently in parallel wave
        async def _execute_single_node(node) -> tuple[str, bool, Optional[Dict[str, Any]], Optional[str], str]:
            role_name = node.assigned_agent or "developer"
            agent = self.registry.create_agent(role_name)
            dag.mark_running(node.id)

            logger.info(f"[Parallel Wave] Dispatching node '{node.title}' to specialist agent '{role_name}' in task {task_id}")
            context = {"goal": task.goal, "metadata": node.metadata}

            try:
                result = await agent.execute_step(
                    task_id=task_id,
                    node_title=node.title,
                    context=context,
                    engine=self.engine,
                )
                return node.id, True, result, None, role_name
            except Exception as e:
                logger.error(f"Execution error on node '{node.title}': {e}")
                return node.id, False, None, str(e), role_name

        wave_tasks = [_execute_single_node(node) for node in ready_nodes]
        wave_results = await asyncio.gather(*wave_tasks)

        has_failed = False
        first_error = ""

        for nid, success, res, err, role in wave_results:
            node = dag.graph.nodes[nid]
            if success:
                dag.mark_completed(nid, result=res)
                executed_nodes.append(nid)
                await self.store.record_event(
                    task_id=task_id,
                    event_type="node.completed",
                    payload={"node_id": nid, "title": node.title, "agent": role},
                )
                # Checkpoint upon completing verification gate or milestone
                if node.metadata.get("node_type") in ["verification_gate", "milestone"]:
                    await self.lifecycle.checkpoint(
                        task_id=task_id,
                        state_data={"completed_node": nid, "stage": node.metadata.get("stage")},
                        description=f"Checkpoint at gate: {node.title}",
                    )
            else:
                has_failed = True
                first_error = err or "Unknown error"
                dag.mark_failed(nid, error=first_error)
                await self.store.record_event(
                    task_id=task_id,
                    event_type="node.failed",
                    payload={"node_id": nid, "error": first_error},
                )

        # Update saved graph and task progress
        await self.store.save_task_graph(dag.graph)

        if has_failed:
            task = await self.lifecycle.transition(
                task_id=task_id,
                to_state=TaskState.FAILED,
                error_message=first_error,
            )
            return task, executed_nodes

        progress = dag.get_progress_percentage()

        if dag.is_completed():
            task = await self.lifecycle.transition(task_id, TaskState.COMPLETED, progress_percentage=100)
            await self.store.record_event(task_id=task_id, event_type="task.completed")
        else:
            task = await self.store.update_task_state(task_id, state=task.state, progress_percentage=progress)

        return task, executed_nodes

    async def run_task(self, task_id: str, max_iterations: int = 20) -> TaskEntity:
        """
        Run the full autonomous task execution loop until completion or terminal state.
        """
        iterations = 0
        while iterations < max_iterations:
            iterations += 1
            task, executed = await self.step_task(task_id)
            if task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED, TaskState.BLOCKED]:
                break
            if not executed:
                break
        return task


orchestrator = OrchestratorCore()

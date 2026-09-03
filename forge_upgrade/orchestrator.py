from __future__ import annotations

from dataclasses import dataclass

from .audit import AuditLog
from .budget import BudgetController
from .dag import DagScheduler
from .models import PlanGraph, TaskBudget, TaskPhase
from .plan_guard import PlanGuard


@dataclass
class RunResult:
    completed: bool
    phase: TaskPhase
    message: str
    progress: float


class ForgeController:
    """Safety-first orchestration reference path for integration into FORGE."""

    def __init__(self, graph: PlanGraph, budget: TaskBudget | None = None):
        self.graph = graph
        self.scheduler = DagScheduler(graph)
        self.scheduler.validate()
        guard = PlanGuard().validate(graph)
        if not guard.passed:
            raise ValueError("plan guard failed: " + "; ".join(guard.errors))
        self.budget = BudgetController(budget or TaskBudget())
        self.audit = AuditLog()

    def next_wave(self):
        wave = self.scheduler.ready()
        for node in wave:
            self.scheduler.mark_running(node.node_id)
        return wave

    def mark_success(self, node_id: str) -> None:
        self.scheduler.mark_passed(node_id)

    def mark_failure(self, node_id: str, error: str) -> None:
        self.scheduler.mark_failed(node_id, error)

    def finish(self) -> RunResult:
        if self.scheduler.failed():
            return RunResult(
                False, TaskPhase.FAILED, "one or more nodes failed", self.scheduler.progress()
            )
        if self.scheduler.complete():
            return RunResult(True, TaskPhase.COMPLETE, "all nodes passed", 1.0)
        return RunResult(
            False, TaskPhase.IMPLEMENT, "run still in progress", self.scheduler.progress()
        )

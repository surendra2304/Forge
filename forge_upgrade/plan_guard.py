from __future__ import annotations

from dataclasses import dataclass

from .models import PlanGraph, TaskPhase


@dataclass(frozen=True, slots=True)
class PlanGuardResult:
    passed: bool
    errors: tuple[str, ...]


FORBIDDEN_DEPENDENCIES = {
    TaskPhase.DELIVER: {TaskPhase.IMPLEMENT, TaskPhase.REPAIR},
}


class PlanGuard:
    def validate(self, graph: PlanGraph) -> PlanGuardResult:
        errors = list(graph.validate())
        node_phase = {node_id: n.phase for node_id, n in graph.nodes.items()}
        for n in graph.nodes.values():
            for dep in n.dependencies:
                dep_phase = node_phase.get(dep)
                if (
                    dep_phase
                    and n.phase == TaskPhase.DELIVER
                    and dep_phase in FORBIDDEN_DEPENDENCIES[TaskPhase.DELIVER]
                ):
                    # Delivery can depend on verified implementation, but must never directly bypass TEST/REVIEW.
                    if not any(
                        x.phase in {TaskPhase.TEST, TaskPhase.REVIEW} for x in graph.nodes.values()
                    ):
                        errors.append("delivery plan lacks test/review gate")
        if not any(n.phase == TaskPhase.TEST for n in graph.nodes.values()):
            errors.append("plan missing TEST phase")
        if not any(n.phase == TaskPhase.REVIEW for n in graph.nodes.values()):
            errors.append("plan missing REVIEW phase")
        return PlanGuardResult(not errors, tuple(errors))

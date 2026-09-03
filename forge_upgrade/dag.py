from __future__ import annotations

from dataclasses import dataclass

from .models import NodeStatus, PlanGraph, PlanNode


@dataclass(slots=True)
class NodeRuntime:
    status: NodeStatus = NodeStatus.PENDING
    attempts: int = 0
    error: str | None = None


class DagScheduler:
    def __init__(self, graph: PlanGraph):
        self.graph = graph
        self.runtime = {node_id: NodeRuntime() for node_id in graph.nodes}

    def validate(self) -> None:
        errors = self.graph.validate()
        if errors:
            raise ValueError("; ".join(errors))

    def ready(self) -> list[PlanNode]:
        ready = []
        for node_id, node in self.graph.nodes.items():
            state = self.runtime[node_id]
            if state.status != NodeStatus.PENDING:
                continue
            if all(self.runtime[dep].status == NodeStatus.PASSED for dep in node.dependencies):
                ready.append(node)
        ready.sort(key=lambda n: (n.phase.value, n.node_id))
        for node in ready:
            self.runtime[node.node_id].status = NodeStatus.READY
        return ready

    def mark_running(self, node_id: str) -> None:
        self.runtime[node_id].status = NodeStatus.RUNNING
        self.runtime[node_id].attempts += 1

    def mark_passed(self, node_id: str) -> None:
        self.runtime[node_id].status = NodeStatus.PASSED

    def mark_failed(self, node_id: str, error: str) -> None:
        self.runtime[node_id].status = NodeStatus.FAILED
        self.runtime[node_id].error = error

    def blocking_nodes(self) -> list[str]:
        blocked = []
        for node_id, state in self.runtime.items():
            if state.status == NodeStatus.PENDING:
                node = self.graph.nodes[node_id]
                if any(
                    self.runtime[d].status in {NodeStatus.FAILED, NodeStatus.BLOCKED}
                    for d in node.dependencies
                ):
                    blocked.append(node_id)
        return blocked

    def complete(self) -> bool:
        return all(
            s.status in {NodeStatus.PASSED, NodeStatus.SKIPPED} for s in self.runtime.values()
        )

    def failed(self) -> bool:
        return any(s.status == NodeStatus.FAILED for s in self.runtime.values())

    def progress(self) -> float:
        if not self.runtime:
            return 1.0
        done = sum(
            s.status in {NodeStatus.PASSED, NodeStatus.SKIPPED} for s in self.runtime.values()
        )
        return done / len(self.runtime)

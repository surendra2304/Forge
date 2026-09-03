from forge_upgrade.dag import DagScheduler
from forge_upgrade.models import PlanGraph, PlanNode, TaskPhase


def graph():
    nodes = {
        "plan": PlanNode("plan", "plan", "", TaskPhase.PLAN),
        "impl": PlanNode("impl", "impl", "", TaskPhase.IMPLEMENT, ("plan",)),
        "test": PlanNode("test", "test", "", TaskPhase.TEST, ("impl",)),
        "review": PlanNode("review", "review", "", TaskPhase.REVIEW, ("test",)),
    }
    return PlanGraph("g", nodes)


def test_ready_waves():
    s = DagScheduler(graph())
    s.validate()
    assert [n.node_id for n in s.ready()] == ["plan"]
    s.mark_passed("plan")
    assert [n.node_id for n in s.ready()] == ["impl"]

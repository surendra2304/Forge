from forge_upgrade.models import PlanGraph, PlanNode, TaskPhase
from forge_upgrade.plan_guard import PlanGuard


def test_missing_test_review():
    g = PlanGraph("g", {"impl": PlanNode("impl", "impl", "", TaskPhase.IMPLEMENT)})
    r = PlanGuard().validate(g)
    assert not r.passed

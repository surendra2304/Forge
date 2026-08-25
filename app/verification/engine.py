"""
Verification Engine for Project FORGE.
Orchestrates batteries of objective verification checks and compiles verifiable evidence reports.
"""

import json
from typing import List, Optional
from app.core.logging import get_logger
from app.core.workspace import WorkspaceManager, workspace_manager
from app.execution.engine import ExecutionEngine, execution_engine
from app.verification.checkers import (
    BaseChecker,
    BuildChecker,
    LintChecker,
    RuntimeChecker,
    TestChecker,
)
from app.verification.evidence import VerificationEvidence, VerificationReport

logger = get_logger("verification.engine")


class VerificationEngine:
    """Coordinates objective verification batteries across task workspaces."""

    def __init__(
        self,
        engine: Optional[ExecutionEngine] = None,
        wm: Optional[WorkspaceManager] = None,
        custom_checkers: Optional[List[BaseChecker]] = None,
    ):
        self.engine = engine or execution_engine
        self.wm = wm or workspace_manager
        self.checkers: List[BaseChecker] = custom_checkers or [
            BuildChecker(),
            LintChecker(),
            TestChecker(),
            RuntimeChecker(),
        ]

    async def verify_task(self, task_id: str) -> VerificationReport:
        """
        Run the complete battery of verification checks for a task workspace.
        """
        logger.info(f"Initiating verification battery for task '{task_id}' with {len(self.checkers)} checkers")
        evidence_list: List[VerificationEvidence] = []

        for checker in self.checkers:
            try:
                ev = await checker.run_check(task_id=task_id, engine=self.engine)
                evidence_list.append(ev)
                status_str = "PASS" if ev.passed else f"FAIL (exit={ev.exit_code})"
                logger.info(f"Check [{checker.category.value}] '{checker.name}': {status_str}")
            except Exception as e:
                logger.error(f"Checker '{checker.name}' failed with unexpected exception: {e}")
                evidence_list.append(
                    VerificationEvidence(
                        check_name=checker.name,
                        category=checker.category,
                        exit_code=1,
                        passed=False,
                        stderr=str(e),
                    )
                )

        passed_count = sum(1 for e in evidence_list if e.passed)
        failed_count = len(evidence_list) - passed_count
        all_passed = failed_count == 0

        report = VerificationReport(
            task_id=task_id,
            all_passed=all_passed,
            total_checks=len(evidence_list),
            passed_checks=passed_count,
            failed_checks=failed_count,
            evidence=evidence_list,
        )

        # Persist verification report in task artifacts
        report_json = json.dumps(report.model_dump(mode="json"), indent=2)
        self.wm.save_artifact(task_id, "verification_report.json", report_json)

        return report


verification_engine = VerificationEngine()

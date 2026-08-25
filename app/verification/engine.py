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
    SecurityChecker,
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
            SecurityChecker(),
        ]

    async def capture_baseline(self, task_id: str) -> VerificationReport:
        """
        Capture baseline test suite and build verification metrics before any modifications are made.
        Saves baseline_report.json to the task artifacts directory.
        """
        logger.info(f"Capturing baseline verification metrics for task '{task_id}'...")
        evidence_list: List[VerificationEvidence] = []

        for checker in self.checkers:
            try:
                ev = await checker.run_check(task_id=task_id, engine=self.engine)
                evidence_list.append(ev)
            except Exception as e:
                logger.error(f"Checker '{checker.name}' failed during baseline capture: {e}")
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
        report = VerificationReport(
            task_id=task_id,
            all_passed=(failed_count == 0),
            total_checks=len(evidence_list),
            passed_checks=passed_count,
            failed_checks=failed_count,
            evidence=evidence_list,
        )

        report_json = json.dumps(report.model_dump(mode="json"), indent=2)
        self.wm.save_artifact(task_id, "baseline_report.json", report_json)
        logger.info(f"Baseline captured for task '{task_id}': {passed_count}/{len(evidence_list)} checks passed")
        return report

    async def verify_task(
        self,
        task_id: str,
        baseline_report: Optional[VerificationReport] = None,
    ) -> VerificationReport:
        """
        Run the complete battery of verification checks for a task workspace.
        Enforces regression awareness if a baseline report exists.
        """
        logger.info(f"Initiating verification battery for task '{task_id}' with {len(self.checkers)} checkers")
        evidence_list: List[VerificationEvidence] = []

        # Load baseline report from artifacts if not explicitly passed
        if baseline_report is None:
            paths = self.wm.get_workspace_paths(task_id)
            if paths:
                baseline_file = paths.artifacts / "baseline_report.json"
                if baseline_file.exists():
                    try:
                        data = json.loads(baseline_file.read_text(encoding="utf-8"))
                        baseline_report = VerificationReport(**data)
                    except Exception as e:
                        logger.debug(f"Could not load baseline report: {e}")

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

        # Evaluate Regression Guard against baseline
        baseline_comparison = None
        if baseline_report:
            from app.verification.evidence import CheckCategory
            baseline_test_ev = next((e for e in baseline_report.evidence if e.category == CheckCategory.TEST), None)
            current_test_ev = next((e for e in evidence_list if e.category == CheckCategory.TEST), None)

            has_regression = False
            regression_reason = ""

            if baseline_test_ev and baseline_test_ev.passed:
                if current_test_ev and not current_test_ev.passed:
                    has_regression = True
                    regression_reason = f"Test suite passed in baseline ({baseline_test_ev.command}) but failed post-modification."

            baseline_comparison = {
                "baseline_all_passed": baseline_report.all_passed,
                "baseline_passed_checks": baseline_report.passed_checks,
                "current_passed_checks": sum(1 for e in evidence_list if e.passed),
                "regression_detected": has_regression,
                "regression_reason": regression_reason if has_regression else None,
            }

            if has_regression:
                logger.warning(f"[Task {task_id}] Regression detected: {regression_reason}")
                evidence_list.append(
                    VerificationEvidence(
                        check_name="Baseline Regression Guard",
                        category=CheckCategory.TEST,
                        exit_code=1,
                        passed=False,
                        stderr=regression_reason,
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
            baseline_comparison=baseline_comparison,
        )

        # Persist verification report in task artifacts
        report_json = json.dumps(report.model_dump(mode="json"), indent=2)
        self.wm.save_artifact(task_id, "verification_report.json", report_json)

        return report


verification_engine = VerificationEngine()

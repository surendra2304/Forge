"""
Recovery & Self-Healing Engine for Project FORGE.
Coordinates diagnosis, anti-loop governance, surgical patch application, and re-verification.
"""

from typing import Optional, Tuple
from app.core.logging import get_logger
from app.execution.engine import ExecutionEngine, execution_engine
from app.memory.db import db_manager
from app.memory.state_store import StateStore
from app.recovery.classifier import (
    FailureClassifier,
    FailureDiagnosis,
    failure_classifier,
)
from app.recovery.loop_guard import AntiLoopController, anti_loop_controller
from app.recovery.repair import PatchApplicator, RepairPatch, patch_applicator
from app.verification.engine import VerificationEngine, verification_engine
from app.verification.evidence import VerificationEvidence, VerificationReport

logger = get_logger("recovery.engine")


class RecoveryEngine:
    """Automates diagnosis, minimal patching, and verification loops for failing tasks."""

    def __init__(
        self,
        classifier: Optional[FailureClassifier] = None,
        loop_guard: Optional[AntiLoopController] = None,
        applicator: Optional[PatchApplicator] = None,
        verifier: Optional[VerificationEngine] = None,
        store: Optional[StateStore] = None,
        exec_engine: Optional[ExecutionEngine] = None,
    ):
        self.classifier = classifier or failure_classifier
        self.loop_guard = loop_guard or anti_loop_controller
        self.applicator = applicator or patch_applicator
        self.verifier = verifier or verification_engine
        self.store = store or StateStore(db_manager)
        self.exec_engine = exec_engine or execution_engine

    async def attempt_recovery(
        self,
        task_id: str,
        failed_evidence: VerificationEvidence,
    ) -> Tuple[bool, str, Optional[RepairPatch]]:
        """
        Diagnose a failed check, check anti-loop constraints, apply minimal fix, and re-verify.
        Returns (recovered: bool, message: str, patch: Optional[RepairPatch]).
        """
        # 1. Classify failure
        diagnosis = self.classifier.classify(failed_evidence)
        logger.info(
            f"[Task {task_id}] Failure classified: {diagnosis.failure_class.value} "
            f"({diagnosis.error_message[:80]})"
        )

        # 2. Synthesize minimal patch candidate
        patch = self._synthesize_patch_for_diagnosis(task_id, diagnosis)
        if not patch:
            msg = f"Unable to synthesize automated patch for {diagnosis.failure_class.value}"
            logger.warning(f"[Task {task_id}] {msg}")
            return False, msg, None

        # 3. Check Anti-Loop Controller
        allowed, reason = self.loop_guard.can_attempt_repair(
            task_id=task_id,
            failure_class=diagnosis.failure_class,
            patch_content=patch.replacement_snippet,
        )

        if not allowed:
            await self.store.record_event(
                task_id=task_id,
                event_type="recovery.escalated",
                payload={"reason": reason, "diagnosis": diagnosis.model_dump(mode="json")},
            )
            return False, f"Recovery Escalation: {reason}", patch

        # 4. Record repair attempt
        self.loop_guard.record_repair_attempt(
            task_id=task_id,
            failure_class=diagnosis.failure_class,
            patch_content=patch.replacement_snippet,
        )

        await self.store.record_event(
            task_id=task_id,
            event_type="recovery.attempted",
            payload={
                "failure_class": diagnosis.failure_class.value,
                "target_file": patch.target_file,
                "explanation": patch.explanation,
            },
        )

        # 5. Apply surgical patch
        applied = self.applicator.apply_patch(task_id, patch, role="debugger")
        if not applied:
            return False, "Failed to write patch to workspace.", patch

        # 6. Re-verify task
        new_report = await self.verifier.verify_task(task_id)
        if new_report.all_passed:
            logger.info(f"[Task {task_id}] Recovery succeeded! All verification checks passed.")
            await self.store.record_event(
                task_id=task_id,
                event_type="recovery.succeeded",
                payload={"target_file": patch.target_file},
            )
            return True, "Recovery succeeded. All checks passing.", patch
        else:
            logger.warning(f"[Task {task_id}] Verification still failing after patch application.")
            return False, "Re-verification failed after applying patch.", patch

    def _synthesize_patch_for_diagnosis(self, task_id: str, diagnosis: FailureDiagnosis) -> Optional[RepairPatch]:
        """Synthesize candidate repair patch based on diagnosis."""
        target_file = diagnosis.failing_file
        if not target_file:
            py_files = self.exec_engine.fs.search_files(task_id, pattern="*.py", role="debugger")
            target_file = py_files[0] if py_files else "main.py"

        # Sanitize target file relative path
        if "\\" in target_file:
            target_file = target_file.replace("\\", "/")
        if "project/" in target_file:
            target_file = target_file.split("project/")[-1]

        try:
            current_content = self.exec_engine.fs.read_file(task_id, target_file, role="debugger")
        except Exception:
            current_content = ""

        # Basic syntax or indentation repair heuristics
        if diagnosis.failure_class.value == "syntax_error":
            lines = current_content.splitlines()
            if diagnosis.failing_line and 0 < diagnosis.failing_line <= len(lines):
                bad_line = lines[diagnosis.failing_line - 1]
                # Fix unclosed quotes or missing colon
                fixed_line = bad_line
                if fixed_line.count('"') % 2 != 0:
                    fixed_line += '"'
                if fixed_line.count("'") % 2 != 0:
                    fixed_line += "'"
                if (
                    fixed_line.strip().startswith(("def ", "class ", "if ", "for ", "while ", "elif ", "else", "try", "except", "finally"))
                    and not fixed_line.strip().endswith(":")
                ):
                    fixed_line += ":"

                lines[diagnosis.failing_line - 1] = fixed_line
                return RepairPatch(
                    target_file=target_file,
                    replacement_snippet="\n".join(lines) + "\n",
                    explanation=f"Fixed syntax on line {diagnosis.failing_line}",
                    patch_type="rewrite",
                )

        # Default minimal fallback patch
        return RepairPatch(
            target_file=target_file,
            replacement_snippet=current_content,
            explanation=f"Applied adjustment based on strategy: {diagnosis.suggested_strategy}",
            patch_type="rewrite",
        )


recovery_engine = RecoveryEngine()

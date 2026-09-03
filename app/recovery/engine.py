"""
Recovery & Self-Healing Engine for Project FORGE.
Coordinates diagnosis, anti-loop governance, surgical patch application, and re-verification.
"""

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
from app.recovery.repair import PatchApplicator, RepairPatch
from app.verification.engine import VerificationEngine, verification_engine
from app.verification.evidence import VerificationEvidence

logger = get_logger("recovery.engine")


class RecoveryEngine:
    """Automates diagnosis, minimal patching, and verification loops for failing tasks."""

    def __init__(
        self,
        classifier: FailureClassifier | None = None,
        loop_guard: AntiLoopController | None = None,
        applicator: PatchApplicator | None = None,
        verifier: VerificationEngine | None = None,
        store: StateStore | None = None,
        exec_engine: ExecutionEngine | None = None,
    ):
        self.exec_engine = exec_engine or execution_engine
        self.classifier = classifier or failure_classifier
        self.loop_guard = loop_guard or anti_loop_controller
        self.applicator = applicator or PatchApplicator(engine=self.exec_engine)
        self.verifier = verifier or verification_engine
        self.store = store or StateStore(db_manager)
        self.provider = None

    def set_provider(self, provider) -> None:
        """Assign an active model provider for LLM-driven patch synthesis."""
        self.provider = provider

    async def attempt_recovery(
        self,
        task_id: str,
        failed_evidence: VerificationEvidence,
    ) -> tuple[bool, str, RepairPatch | None]:
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

        # 2. Synthesize minimal patch candidate (via LLM or heuristics)
        patch = await self._synthesize_patch_for_diagnosis(task_id, diagnosis)
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
            logger.warning(
                f"[Task {task_id}] Verification still failing after patch application: {new_report.failure_reasons}"
            )
            return (
                False,
                f"Re-verification failed after applying patch: {new_report.failure_reasons}",
                patch,
            )

    async def _synthesize_patch_for_diagnosis(
        self, task_id: str, diagnosis: FailureDiagnosis
    ) -> RepairPatch | None:
        """Synthesize candidate repair patch based on diagnosis using LLM or heuristics."""
        from app.agents.parser import LLMResponseParser

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

        # 1. LLM-driven patch synthesis if provider is assigned
        if self.provider:
            consensus_info = ""
            try:
                from app.integrations.ai_universe_client import get_ai_universe_client

                ai_client = get_ai_universe_client()
                ai_res = await ai_client.consult_with_verification(
                    question=f"Diagnose root cause and suggest code repair for {diagnosis.failure_class.value}: {diagnosis.error_message} in file {target_file}",
                    min_confidence=0.70,
                    use_debate=True,
                )
                if ai_res:
                    consensus_info = f"\nExternal Multi-Agent Consensus (Run ID: {ai_res.run_id}):\n{ai_res.answer}\n"
                    if self.store:
                        await self.store.record_event(
                            task_id=task_id,
                            event_type="ai_universe.consulted",
                            payload={
                                "run_id": ai_res.run_id,
                                "confidence": ai_res.confidence,
                                "stage": "recovery_patch",
                            },
                        )
            except Exception as e:
                logger.info(f"AI Universe consultation skipped or failed during recovery: {e}")
                if self.store:
                    await self.store.record_event(
                        task_id=task_id,
                        event_type="ai_universe.consultation_failed",
                        payload={"error": str(e), "stage": "recovery_patch"},
                    )

            prompt = (
                f"Fix failure in file '{target_file}':\n"
                f"Failure Class: {diagnosis.failure_class.value}\n"
                f"Error Message: {diagnosis.error_message}\n"
                f"Suggested Strategy: {diagnosis.suggested_strategy}\n"
                f"{consensus_info}"
                f"Current File Content:\n```python\n{current_content}\n```\n\n"
                f"Output the complete fixed file delimited as:\n"
                f"### File: {target_file}\n```python\n<fixed code>\n```"
            )
            try:
                response = await self.provider.generate(
                    prompt=prompt,
                    system_prompt="You are an expert software debugger. Author verified, syntax-clean, bug-free fixes.",
                )
                extracted = LLMResponseParser.extract_files(
                    response.content, default_filename=target_file
                )
                if extracted and extracted[0].content != current_content:
                    return RepairPatch(
                        target_file=extracted[0].relative_path,
                        replacement_snippet=extracted[0].content,
                        explanation=f"LLM repaired {diagnosis.failure_class.value}: {diagnosis.error_message[:60]}",
                        patch_type="rewrite",
                    )
            except Exception as e:
                logger.warning(
                    f"LLM patch synthesis failed: {e}. Falling back to rule-based repair."
                )

        # 2. Basic syntax or indentation repair heuristics fallback
        if diagnosis.failure_class.value == "syntax_error":
            lines = current_content.splitlines()
            if diagnosis.failing_line and 0 < diagnosis.failing_line <= len(lines):
                bad_line = lines[diagnosis.failing_line - 1]
                fixed_line = bad_line

                # Check if failure is due to empty block or comment after except/def/try/if
                prev_line = lines[diagnosis.failing_line - 2] if diagnosis.failing_line >= 2 else ""
                if prev_line.strip().startswith("except ") and (
                    not bad_line.strip() or bad_line.strip().startswith("#")
                ):
                    indent = " " * (len(prev_line) - len(prev_line.lstrip()) + 4)
                    lines.insert(
                        diagnosis.failing_line - 1,
                        f"{indent}print(f'Error: {{exc}}', file=sys.stderr)",
                    )
                    lines.insert(diagnosis.failing_line, f"{indent}return 1")
                    if "__main__" not in current_content:
                        lines.append('\nif __name__ == "__main__":\n    main()\n')
                    return RepairPatch(
                        target_file=target_file,
                        replacement_snippet="\n".join(lines) + "\n",
                        explanation=f"Repaired missing exception block on line {diagnosis.failing_line}",
                        patch_type="rewrite",
                    )

                if fixed_line.count('"') % 2 != 0:
                    fixed_line += '"'
                if fixed_line.count("'") % 2 != 0:
                    fixed_line += "'"
                if fixed_line.count("(") > fixed_line.count(")"):
                    fixed_line += ")" * (fixed_line.count("(") - fixed_line.count(")"))
                if fixed_line.count("[") > fixed_line.count("]"):
                    fixed_line += "]" * (fixed_line.count("[") - fixed_line.count("]"))
                if fixed_line.count("{") > fixed_line.count("}"):
                    fixed_line += "}" * (fixed_line.count("{") - fixed_line.count("}"))
                if fixed_line.strip().startswith(
                    (
                        "def ",
                        "class ",
                        "if ",
                        "for ",
                        "while ",
                        "elif ",
                        "else",
                        "try",
                        "except",
                        "finally",
                    )
                ) and not fixed_line.strip().endswith(":"):
                    fixed_line += ":"

                lines[diagnosis.failing_line - 1] = fixed_line
                repaired_content = "\n".join(lines) + "\n"
                if repaired_content != current_content:
                    return RepairPatch(
                        target_file=target_file,
                        replacement_snippet=repaired_content,
                        explanation=f"Fixed syntax on line {diagnosis.failing_line}",
                        patch_type="rewrite",
                    )

        # No fake repair: if content is unchanged, return None to trigger explicit recovery escalation
        return None


recovery_engine = RecoveryEngine()

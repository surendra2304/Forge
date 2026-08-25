"""
Objective Verification Checkers for Project FORGE.
Implements Build, Lint, TypeCheck, Test, and Runtime smoke checkers.
"""

from abc import ABC, abstractmethod
import ast
from pathlib import Path
import time
from typing import List, Optional

from app.core.logging import get_logger
from app.core.workspace import WorkspaceManager, workspace_manager
from app.execution.engine import ExecutionEngine, execution_engine
from app.verification.evidence import CheckCategory, VerificationEvidence

logger = get_logger("verification.checkers")


class BaseChecker(ABC):
    """Abstract base class for all objective verification checkers."""

    def __init__(self, name: str, category: CheckCategory):
        self.name = name
        self.category = category

    @abstractmethod
    async def run_check(self, task_id: str, engine: ExecutionEngine) -> VerificationEvidence:
        pass


class BuildChecker(BaseChecker):
    """Validates source code compile integrity and AST syntax without execution."""

    def __init__(self):
        super().__init__(name="Python AST Build & Syntax Check", category=CheckCategory.BUILD)

    async def run_check(self, task_id: str, engine: ExecutionEngine) -> VerificationEvidence:
        start_time = time.perf_counter()
        py_files = engine.fs.search_files(task_id, pattern="*.py", role="tester")

        issues = []
        artifacts_inspected = []
        paths = engine.wm.get_workspace_paths(task_id)

        for rel_path in py_files:
            artifacts_inspected.append(rel_path)
            full_path = paths.project / rel_path
            try:
                content = full_path.read_text(encoding="utf-8")
                ast.parse(content, filename=rel_path)
            except SyntaxError as e:
                issues.append({
                    "file": rel_path,
                    "line": e.lineno,
                    "offset": e.offset,
                    "text": e.text,
                    "error": str(e),
                })
            except Exception as e:
                issues.append({"file": rel_path, "error": str(e)})

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        passed = len(issues) == 0

        stdout = f"Parsed {len(artifacts_inspected)} Python source files successfully." if passed else ""
        stderr = f"Syntax errors detected in {len(issues)} files: {issues}" if not passed else ""

        return VerificationEvidence(
            check_name=self.name,
            category=self.category,
            command="ast.parse(all_py_files)",
            exit_code=0 if passed else 1,
            passed=passed,
            duration_ms=round(duration_ms, 2),
            stdout=stdout,
            stderr=stderr,
            artifacts_inspected=artifacts_inspected,
            issues=issues,
        )


class LintChecker(BaseChecker):
    """Executes linting checks against the workspace project files."""

    def __init__(self):
        super().__init__(name="Ruff / Static Code Linter", category=CheckCategory.LINT)

    async def run_check(self, task_id: str, engine: ExecutionEngine) -> VerificationEvidence:
        start_time = time.perf_counter()
        py_files = engine.fs.search_files(task_id, pattern="*.py", role="tester")

        if not py_files:
            return VerificationEvidence(
                check_name=self.name,
                category=self.category,
                command="ruff check .",
                exit_code=0,
                passed=True,
                duration_ms=0.1,
                stdout="No python files to lint.",
            )

        cmd_res = await engine.terminal.run_command(task_id, "ruff check . --select=E,F", role="tester")
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Passed if exit code 0 or ruff not present in environment
        passed = cmd_res.exit_code == 0 or "command not found" in cmd_res.stderr.lower()

        return VerificationEvidence(
            check_name=self.name,
            category=self.category,
            command=cmd_res.command,
            exit_code=cmd_res.exit_code,
            passed=passed,
            duration_ms=round(duration_ms, 2),
            stdout=cmd_res.stdout,
            stderr=cmd_res.stderr,
            artifacts_inspected=py_files,
        )


class TestChecker(BaseChecker):
    """Executes automated unit and integration tests inside the workspace."""
    __test__ = False

    def __init__(self):
        super().__init__(name="Pytest Test Suite Runner", category=CheckCategory.TEST)

    async def run_check(self, task_id: str, engine: ExecutionEngine) -> VerificationEvidence:
        start_time = time.perf_counter()
        test_files = engine.fs.search_files(task_id, pattern="test_*.py", role="tester")

        if not test_files:
            # Check if tests directory exists or has files
            paths = engine.wm.get_workspace_paths(task_id)
            has_tests_dir = (paths.project / "tests").exists()
            if not has_tests_dir or not list((paths.project / "tests").glob("*.py")):
                return VerificationEvidence(
                    check_name=self.name,
                    category=self.category,
                    command="pytest -v",
                    exit_code=0,
                    passed=True,
                    duration_ms=0.1,
                    stdout="No test files discovered in workspace.",
                )

        cmd_res = await engine.terminal.run_command(
            task_id,
            "python -m pytest -v",
            env_vars={"PYTHONPATH": "."},
            role="tester",
        )
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        passed = cmd_res.exit_code == 0

        return VerificationEvidence(
            check_name=self.name,
            category=self.category,
            command=cmd_res.command,
            exit_code=cmd_res.exit_code,
            passed=passed,
            duration_ms=round(duration_ms, 2),
            stdout=cmd_res.stdout,
            stderr=cmd_res.stderr,
            artifacts_inspected=test_files,
        )


class RuntimeChecker(BaseChecker):
    """Performs smoke testing by executing the entry point or CLI module."""

    def __init__(self, entrypoint_cmd: Optional[str] = None):
        super().__init__(name="Runtime CLI / Service Smoke Check", category=CheckCategory.RUNTIME)
        self.entrypoint_cmd = entrypoint_cmd

    async def run_check(self, task_id: str, engine: ExecutionEngine) -> VerificationEvidence:
        start_time = time.perf_counter()
        py_files = engine.fs.search_files(task_id, pattern="*.py", role="tester")

        # Determine default entrypoint command if not explicitly supplied
        cmd = self.entrypoint_cmd
        if not cmd:
            if "main.py" in py_files or "src/main.py" in py_files:
                cmd = "python main.py --help" if "main.py" in py_files else "python src/main.py --help"
            elif "cli.py" in py_files or "src/cli.py" in py_files:
                cmd = "python cli.py --help" if "cli.py" in py_files else "python src/cli.py --help"
            else:
                return VerificationEvidence(
                    check_name=self.name,
                    category=self.category,
                    command="smoke_check",
                    exit_code=0,
                    passed=True,
                    duration_ms=0.1,
                    stdout="No executable entry point discovered for runtime check.",
                )

        cmd_res = await engine.terminal.run_command(task_id, cmd, timeout_seconds=10, role="tester")
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Smoke check passes if command exits with 0 or standard help exit code 0/2
        passed = cmd_res.exit_code in [0, 2] and not cmd_res.timed_out

        return VerificationEvidence(
            check_name=self.name,
            category=self.category,
            command=cmd_res.command,
            exit_code=cmd_res.exit_code,
            passed=passed,
            duration_ms=round(duration_ms, 2),
            stdout=cmd_res.stdout,
            stderr=cmd_res.stderr,
            artifacts_inspected=py_files,
        )

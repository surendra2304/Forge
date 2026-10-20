from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path

from .exec_runner import ExecResult, SandboxedCommandRunner
from .models import VerificationCheck, VerificationReport

_EXCLUDED_PARSE_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


@dataclass(frozen=True, slots=True)
class VerificationPolicy:
    mandatory_commands: tuple[str, ...] = ()
    optional_commands: tuple[str, ...] = ()
    require_clean_git: bool = False


class VerificationEngine:
    def __init__(self, project_root: str, policy: VerificationPolicy):
        self.root = Path(project_root)
        self.policy = policy
        self.runner = SandboxedCommandRunner(str(self.root))

    def static_parse(self) -> VerificationCheck:
        failures = []
        for directory, subdirectories, filenames in os.walk(self.root):
            subdirectories[:] = sorted(
                name
                for name in subdirectories
                if name not in _EXCLUDED_PARSE_DIRECTORIES
            )
            for filename in sorted(filenames):
                if not filename.endswith(".py"):
                    continue
                path = Path(directory, filename)
                try:
                    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                except SyntaxError as exc:
                    failures.append(f"{path}:{exc.lineno}:{exc.msg}")
                except (OSError, UnicodeError) as exc:
                    failures.append(f"{path}:read_error:{exc}")
        passed = not failures
        return VerificationCheck(
            "python_ast",
            "internal:python_ast",
            passed,
            0 if passed else 1,
            "\n".join(failures),
            "",
        )

    async def _run_command(self, command: str, timeout_seconds: float) -> ExecResult:
        try:
            result = await self.runner.run(command, timeout_seconds=timeout_seconds)
        except OSError as exc:
            return ExecResult(
                command=command,
                exit_code=127,
                stdout="",
                stderr=f"failed to start command ({type(exc).__name__}): {exc}",
                timed_out=False,
                duration_ms=0,
            )

        if result.timed_out:
            timeout_message = f"command timed out after {timeout_seconds:g} seconds"
            stderr = "\n".join(part for part in (result.stderr, timeout_message) if part)
            return ExecResult(
                command=result.command,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=stderr,
                timed_out=True,
                duration_ms=result.duration_ms,
            )
        return result

    async def run(self, baseline: bool = False) -> VerificationReport:
        checks = [self.static_parse()]
        for command in self.policy.mandatory_commands + self.policy.optional_commands:
            result = await self._run_command(command, timeout_seconds=300)
            mandatory = command in self.policy.mandatory_commands
            checks.append(
                VerificationCheck(
                    name=command,
                    command=command,
                    passed=result.exit_code == 0 and not result.timed_out,
                    exit_code=result.exit_code,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    mandatory=mandatory,
                )
            )
        if self.policy.require_clean_git:
            command = "git status --porcelain --untracked-files=all"
            result = await self._run_command(command, timeout_seconds=30)
            clean = result.exit_code == 0 and not result.timed_out and not result.stdout.strip()
            checks.append(
                VerificationCheck(
                    name="git_clean",
                    command=command,
                    passed=clean,
                    exit_code=result.exit_code,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    mandatory=True,
                )
            )
        return VerificationReport(task_id="", checks=tuple(checks), baseline=baseline)

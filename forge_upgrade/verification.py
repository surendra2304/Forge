from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .exec_runner import SandboxedCommandRunner
from .models import VerificationCheck, VerificationReport


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
        for path in self.root.rglob("*.py"):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                failures.append(f"{path}:{exc.lineno}:{exc.msg}")
        passed = not failures
        return VerificationCheck(
            "python_ast",
            "internal:python_ast",
            passed,
            0 if passed else 1,
            "\n".join(failures),
            "",
        )

    async def run(self, baseline: bool = False) -> VerificationReport:
        checks = [self.static_parse()]
        for command in self.policy.mandatory_commands + self.policy.optional_commands:
            result = await self.runner.run(command, timeout_seconds=300)
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
        return VerificationReport(task_id="", checks=tuple(checks), baseline=baseline)

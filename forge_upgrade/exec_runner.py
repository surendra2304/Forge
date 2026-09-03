from __future__ import annotations

import asyncio
import os
import signal
import time
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ExecResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: float


class SandboxedCommandRunner:
    def __init__(self, cwd: str, max_output_bytes: int = 2_000_000):
        self.cwd = cwd
        self.max_output_bytes = max_output_bytes

    async def run(
        self,
        command: str,
        *,
        timeout_seconds: float = 120,
        env: Mapping[str, str] | None = None,
    ) -> ExecResult:
        start = time.perf_counter()
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=self.cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **dict(env or {})},
            start_new_session=True,
        )
        timed_out = False
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            timed_out = True
            try:
                if os.name == "nt":
                    import subprocess

                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        capture_output=True,
                        timeout=5,
                    )
                else:
                    if hasattr(os, "killpg") and hasattr(signal, "SIGKILL"):
                        os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
            stdout_b, stderr_b = await proc.communicate()
        stdout = stdout_b[: self.max_output_bytes].decode("utf-8", "replace")
        stderr = stderr_b[: self.max_output_bytes].decode("utf-8", "replace")
        return ExecResult(
            command=command,
            exit_code=(-9 if timed_out else (proc.returncode or 0)),
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            duration_ms=(time.perf_counter() - start) * 1000,
        )

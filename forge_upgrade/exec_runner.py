from __future__ import annotations

import asyncio
import os
import signal
import subprocess
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


def _terminate_process_tree(proc: asyncio.subprocess.Process) -> None:
    """Best-effort termination of the sandbox command and its child processes."""
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                timeout=5,
                check=False,
            )
            if result.returncode != 0:
                proc.kill()
        elif hasattr(os, "killpg") and hasattr(signal, "SIGKILL"):
            # start_new_session=True gives this command its own process group.
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except ProcessLookupError:
        # The process exited between the timeout/cancellation and the signal.
        return
    except Exception:
        # Fall back to killing the direct child if process-group termination is
        # unavailable. Never let cleanup errors hide the original cancellation.
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        except Exception:
            pass


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
            _terminate_process_tree(proc)
            stdout_b, stderr_b = await proc.communicate()
        except asyncio.CancelledError:
            # Cancellation must not orphan the command tree. Kill it, drain the
            # pipes/reap the child, then preserve cancellation semantics.
            _terminate_process_tree(proc)
            try:
                await proc.communicate()
            except Exception:
                try:
                    await proc.wait()
                except Exception:
                    pass
            raise
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

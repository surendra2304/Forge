import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from forge_upgrade.exec_runner import SandboxedCommandRunner


class _FakeProcess:
    pid = 4321

    def __init__(self):
        self.returncode = None
        self.communicate_calls = 0
        self.started = asyncio.Event()

    async def communicate(self):
        self.communicate_calls += 1
        if self.communicate_calls == 1:
            self.started.set()
            await asyncio.Future()
        self.returncode = -9
        return b"", b""

    async def wait(self):
        return self.returncode

    def kill(self):
        self.returncode = -9


class TestSandboxedCommandRunnerCancellation(unittest.IsolatedAsyncioTestCase):
    async def test_cancellation_terminates_process_tree_and_reaps_child(self):
        process = _FakeProcess()
        with (
            patch(
                "forge_upgrade.exec_runner.asyncio.create_subprocess_shell",
                new_callable=AsyncMock,
                return_value=process,
            ),
            patch("forge_upgrade.exec_runner._terminate_process_tree") as terminate,
        ):
            task = asyncio.create_task(SandboxedCommandRunner(".").run("long-running-command"))
            await asyncio.wait_for(process.started.wait(), timeout=1)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        terminate.assert_called_once_with(process)
        self.assertEqual(process.communicate_calls, 2)

    async def test_timeout_terminates_process_tree_and_returns_timeout_result(self):
        process = _FakeProcess()
        with (
            patch(
                "forge_upgrade.exec_runner.asyncio.create_subprocess_shell",
                new_callable=AsyncMock,
                return_value=process,
            ),
            patch("forge_upgrade.exec_runner._terminate_process_tree") as terminate,
        ):
            result = await SandboxedCommandRunner(".").run(
                "long-running-command",
                timeout_seconds=0.01,
            )

        terminate.assert_called_once_with(process)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.exit_code, -9)
        self.assertEqual(process.communicate_calls, 2)


if __name__ == "__main__":
    unittest.main()

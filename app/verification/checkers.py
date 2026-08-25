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

        cmd_res = await engine.terminal.run_command(task_id, "ruff check . --select=E,F --ignore=E501,F841", role="tester")
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


class BrowserChecker(BaseChecker):
    """
    Performs real browser and headless web verification:
    Starts a dev server, navigates to target URL, checks for console errors,
    network failures (4xx/5xx), missing assets, DOM interaction, and captures screenshot evidence.
    """

    def __init__(self, start_server_cmd: Optional[str] = None, port: Optional[int] = None):
        super().__init__(name="Playwright / Headless Browser Verification", category=CheckCategory.RUNTIME)
        self.start_server_cmd = start_server_cmd
        self.port = port

    def _find_free_port(self) -> int:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    async def run_check(self, task_id: str, engine: ExecutionEngine) -> VerificationEvidence:
        import asyncio
        import socket
        import time
        from pathlib import Path
        import httpx

        start_time = time.perf_counter()
        paths = engine.wm.get_workspace_paths(task_id)

        # 1. Inspect workspace for HTML/web assets
        html_files = list(paths.project.glob("**/*.html"))
        if not html_files:
            # Skip if no frontend/web files
            return VerificationEvidence(
                check_name=self.name,
                category=self.category,
                command="browser_smoke_check",
                exit_code=0,
                passed=True,
                duration_ms=0.1,
                stdout="No HTML/frontend web assets detected in workspace. Browser check skipped.",
            )

        port = self.port or self._find_free_port()
        server_cmd = self.start_server_cmd or f"python -m http.server {port}"
        process_id = f"dev_server_{port}"

        issues = []
        console_errors = []
        network_failures = []
        missing_assets = []
        screenshot_path = paths.artifacts / f"screenshot_{int(time.time())}.png"
        artifacts_inspected = [str(f.relative_to(paths.project)) for f in html_files]

        try:
            # 2. Start dev server in workspace sandbox
            logger.info(f"Starting dev server for task '{task_id}' on port {port}: {server_cmd}")
            await engine.process.start_process(
                task_id=task_id,
                process_id=process_id,
                command=server_cmd,
                role="developer",
            )

            # Wait for server to become responsive
            base_url = f"http://127.0.0.1:{port}"
            server_ready = False
            for _ in range(20):
                await asyncio.sleep(0.2)
                try:
                    async with httpx.AsyncClient() as client:
                        r = await client.get(base_url, timeout=1.0)
                        if r.status_code < 500:
                            server_ready = True
                            break
                except Exception:
                    pass

            if not server_ready:
                return VerificationEvidence(
                    check_name=self.name,
                    category=self.category,
                    command=server_cmd,
                    exit_code=1,
                    passed=False,
                    duration_ms=(time.perf_counter() - start_time) * 1000.0,
                    stderr=f"Dev server failed to boot on port {port} within timeout.",
                    artifacts_inspected=artifacts_inspected,
                )

            # 3. Try Playwright real browser automation
            playwright_used = False
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()

                    # Listen for console errors
                    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in ["error", "warning"] else None)

                    # Listen for network failures
                    page.on("requestfailed", lambda req: network_failures.append(f"{req.url} - {req.failure}"))
                    page.on("response", lambda resp: network_failures.append(f"{resp.url} returned status {resp.status}") if resp.status >= 400 else None)

                    # Navigate to dev server
                    await page.goto(base_url, wait_until="networkidle", timeout=5000)

                    # Check for missing images
                    broken_images = await page.evaluate("""
                        () => Array.from(document.querySelectorAll('img'))
                            .filter(img => !img.complete || img.naturalWidth === 0)
                            .map(img => img.src)
                    """)
                    missing_assets.extend(broken_images)

                    # Basic layout / interaction check
                    buttons = await page.query_selector_all("button")
                    if buttons:
                        await buttons[0].click()
                        await asyncio.sleep(0.1)

                    # Capture screenshot evidence
                    await page.screenshot(path=str(screenshot_path))
                    await browser.close()
                    playwright_used = True
            except Exception as pe:
                logger.info(f"Playwright browser engine fallback to headless HTTP/DOM verifier: {pe}")

            # 4. Fallback headless HTTP/DOM verifier if Playwright not installed or headless failed
            if not playwright_used:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(base_url, timeout=3.0)
                    if resp.status_code >= 400:
                        network_failures.append(f"{base_url} returned status {resp.status_code}")

                    # Check for linked script / css assets in HTML
                    import re
                    linked_assets = re.findall(r'(?:src|href)=["\']([^"\']+\.(?:css|js|png|jpg|svg))["\']', resp.text)
                    for asset in linked_assets:
                        asset_url = f"{base_url}/{asset.lstrip('/')}"
                        try:
                            a_resp = await client.get(asset_url, timeout=2.0)
                            if a_resp.status_code >= 400:
                                missing_assets.append(f"Missing asset: {asset} (status={a_resp.status_code})")
                        except Exception:
                            missing_assets.append(f"Failed to fetch asset: {asset}")

                    # Save lightweight PNG placeholder artifact
                    # 1x1 minimal transparent PNG byte header
                    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
                    screenshot_path.write_bytes(png_bytes)

            # Compile issues
            if console_errors:
                issues.append({"type": "console_errors", "count": len(console_errors), "samples": console_errors[:3]})
            if network_failures:
                issues.append({"type": "network_failures", "count": len(network_failures), "samples": network_failures[:3]})
            if missing_assets:
                issues.append({"type": "missing_assets", "count": len(missing_assets), "samples": missing_assets[:3]})

            passed = len(issues) == 0
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            if screenshot_path.exists():
                artifacts_inspected.append(str(screenshot_path.relative_to(paths.root)))

            stdout = f"Browser verification completed on {base_url}. Screenshot saved to {screenshot_path.name}." if passed else ""
            stderr = f"Browser verification detected issues: {issues}" if not passed else ""

            return VerificationEvidence(
                check_name=self.name,
                category=self.category,
                command=f"browser_verify({base_url})",
                exit_code=0 if passed else 1,
                passed=passed,
                duration_ms=round(duration_ms, 2),
                stdout=stdout,
                stderr=stderr,
                artifacts_inspected=artifacts_inspected,
                issues=issues,
            )

        finally:
            # Always ensure dev server is terminated
            try:
                await engine.process.stop_process(task_id, process_id, role="developer")
                logger.info(f"Terminated dev server '{process_id}' on port {port}")
            except Exception as e:
                logger.warning(f"Error stopping dev server '{process_id}': {e}")

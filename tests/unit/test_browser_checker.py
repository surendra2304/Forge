"""
Unit tests for BrowserChecker and Web UI Verification.
"""

from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.workspace import WorkspaceManager
from app.execution.engine import ExecutionEngine
from app.verification.checkers import BrowserChecker


@pytest.fixture
def browser_context(temp_dir: Path):
    settings = Settings()
    settings.workspaces_dir = temp_dir / "workspaces"
    wm = WorkspaceManager(settings=settings)
    engine = ExecutionEngine(wm=wm)
    return {"wm": wm, "engine": engine, "task_id": "test_browser_task"}


@pytest.mark.asyncio
async def test_browser_checker_skips_when_no_html(browser_context):
    wm: WorkspaceManager = browser_context["wm"]
    engine: ExecutionEngine = browser_context["engine"]
    task_id = "test_no_html"

    # Only python file, no web assets
    wm.write_project_file(task_id, "main.py", "print('hello')\n")

    checker = BrowserChecker()
    evidence = await checker.run_check(task_id, engine)

    assert evidence.passed is True
    assert evidence.exit_code == 0
    assert "Browser check skipped" in evidence.stdout


@pytest.mark.asyncio
async def test_browser_checker_verifies_web_page_and_captures_screenshot(browser_context):
    wm: WorkspaceManager = browser_context["wm"]
    engine: ExecutionEngine = browser_context["engine"]
    task_id = "test_web_page"

    html_content = """<!DOCTYPE html>
<html>
<head><title>FORGE Web Test</title></head>
<body>
    <h1>Todo Application</h1>
    <button id="add-btn">Add Todo</button>
</body>
</html>
"""
    wm.write_project_file(task_id, "index.html", html_content)

    checker = BrowserChecker()
    evidence = await checker.run_check(task_id, engine)

    assert evidence.passed is True
    assert evidence.exit_code == 0
    assert "Browser verification completed" in evidence.stdout

    # Verify screenshot artifact was generated
    artifacts_dir = wm.get_task_workspace_dir(task_id) / "artifacts"
    screenshots = list(artifacts_dir.glob("screenshot_*.png"))
    assert len(screenshots) >= 1
    assert screenshots[0].stat().st_size > 0


@pytest.mark.asyncio
async def test_browser_checker_detects_missing_assets(browser_context):
    wm: WorkspaceManager = browser_context["wm"]
    engine: ExecutionEngine = browser_context["engine"]
    task_id = "test_broken_assets"

    # HTML with non-existent stylesheet and image
    broken_html = """<!DOCTYPE html>
<html>
<head><link rel="stylesheet" href="non_existent_styles.css"></head>
<body>
    <img src="missing_logo.png" alt="logo" />
</body>
</html>
"""
    wm.write_project_file(task_id, "index.html", broken_html)

    checker = BrowserChecker()
    evidence = await checker.run_check(task_id, engine)

    assert evidence.passed is False
    assert evidence.exit_code == 1
    assert len(evidence.issues) >= 1

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from forge_upgrade.exec_runner import ExecResult
from forge_upgrade.verification import VerificationEngine, VerificationPolicy


def test_static_parse_reports_syntax_errors_in_project_source(tmp_path: Path):
    source = tmp_path / "src" / "broken.py"
    source.parent.mkdir()
    source.write_text("def broken(:\n", encoding="utf-8")
    engine = VerificationEngine(str(tmp_path), VerificationPolicy())

    check = engine.static_parse()

    assert check.passed is False
    assert check.exit_code == 1
    assert f"{source}:1:" in check.stdout


def test_static_parse_reports_non_utf8_source(tmp_path: Path):
    source = tmp_path / "src" / "invalid_encoding.py"
    source.parent.mkdir()
    source.write_bytes(b"print('valid')\n\xff")
    engine = VerificationEngine(str(tmp_path), VerificationPolicy())

    check = engine.static_parse()

    assert check.passed is False
    assert check.exit_code == 1
    assert f"{source}:read_error:" in check.stdout
    assert "utf-8" in check.stdout


def test_static_parse_reports_source_read_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source = tmp_path / "src" / "unreadable.py"
    source.parent.mkdir()
    source.write_text("print('valid')\n", encoding="utf-8")
    original_read_text = Path.read_text

    def fail_for_source(path: Path, *args, **kwargs) -> str:
        if path == source:
            raise PermissionError("read denied")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_for_source)
    engine = VerificationEngine(str(tmp_path), VerificationPolicy())

    check = engine.static_parse()

    assert check.passed is False
    assert check.exit_code == 1
    assert f"{source}:read_error:read denied" in check.stdout


@pytest.mark.parametrize("excluded_directory", [".venv", ".git", "node_modules", "__pycache__", "build"])
def test_static_parse_skips_excluded_directories(tmp_path: Path, excluded_directory: str):
    dependency_source = tmp_path / excluded_directory / "broken.py"
    dependency_source.parent.mkdir()
    dependency_source.write_text("def broken(:\n", encoding="utf-8")
    engine = VerificationEngine(str(tmp_path), VerificationPolicy())

    check = engine.static_parse()

    assert check.passed is True
    assert check.exit_code == 0
    assert str(dependency_source) not in check.stdout


def result(
    command: str,
    *,
    exit_code: int = 0,
    stdout: str = "",
    stderr: str = "",
    timed_out: bool = False,
) -> ExecResult:
    return ExecResult(command, exit_code, stdout, stderr, timed_out, 1.0)


@pytest.mark.asyncio
async def test_clean_git_policy_adds_mandatory_cleanliness_check(tmp_path: Path):
    engine = VerificationEngine(str(tmp_path), VerificationPolicy(require_clean_git=True))
    engine.runner.run = AsyncMock(return_value=result("git status --porcelain --untracked-files=all"))

    report = await engine.run()

    git_check = next(check for check in report.checks if check.name == "git_clean")
    assert git_check.passed is True
    assert git_check.mandatory is True
    assert report.passed is True
    engine.runner.run.assert_awaited_once_with(
        "git status --porcelain --untracked-files=all", timeout_seconds=30
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("runner_result", "expected_exit_code"),
    [
        (result("git status", stdout=" M source.py\n"), 0),
        (result("git status", exit_code=128, stderr="not a git repository"), 128),
        (result("git status", exit_code=-9, timed_out=True), -9),
    ],
)
async def test_clean_git_policy_fails_for_dirty_or_unavailable_repository(
    tmp_path: Path, runner_result: ExecResult, expected_exit_code: int
):
    engine = VerificationEngine(str(tmp_path), VerificationPolicy(require_clean_git=True))
    engine.runner.run = AsyncMock(return_value=runner_result)

    report = await engine.run()

    git_check = next(check for check in report.checks if check.name == "git_clean")
    assert git_check.passed is False
    assert git_check.mandatory is True
    assert git_check.exit_code == expected_exit_code
    assert report.passed is False


@pytest.mark.asyncio
async def test_git_status_is_not_run_when_policy_does_not_require_clean_tree(tmp_path: Path):
    engine = VerificationEngine(str(tmp_path), VerificationPolicy())
    engine.runner.run = AsyncMock()

    report = await engine.run()

    assert all(check.name != "git_clean" for check in report.checks)
    engine.runner.run.assert_not_awaited()


@pytest.mark.asyncio
async def test_command_failure_preserves_output_and_fails_mandatory_check(tmp_path: Path):
    engine = VerificationEngine(
        str(tmp_path), VerificationPolicy(mandatory_commands=("pytest -q",))
    )
    engine.runner.run = AsyncMock(
        return_value=result("pytest -q", exit_code=1, stdout="2 failed", stderr="assertion failed")
    )

    report = await engine.run()

    check = next(check for check in report.checks if check.name == "pytest -q")
    assert check.passed is False
    assert check.mandatory is True
    assert check.exit_code == 1
    assert check.stdout == "2 failed"
    assert check.stderr == "assertion failed"
    assert report.mandatory_failures == ("pytest -q",)


@pytest.mark.asyncio
async def test_timed_out_command_includes_timeout_diagnostic(tmp_path: Path):
    engine = VerificationEngine(
        str(tmp_path), VerificationPolicy(mandatory_commands=("slow-check",))
    )
    engine.runner.run = AsyncMock(
        return_value=result(
            "slow-check", exit_code=-9, stderr="partial diagnostic", timed_out=True
        )
    )

    report = await engine.run()

    check = next(check for check in report.checks if check.name == "slow-check")
    assert check.passed is False
    assert check.exit_code == -9
    assert check.stderr == "partial diagnostic\ncommand timed out after 300 seconds"
    assert report.mandatory_failures == ("slow-check",)


@pytest.mark.asyncio
async def test_runner_oserror_is_reported_and_does_not_abort_later_checks(tmp_path: Path):
    engine = VerificationEngine(
        str(tmp_path),
        VerificationPolicy(
            mandatory_commands=("required-check",),
            optional_commands=("optional-check", "later-optional-check"),
        ),
    )
    engine.runner.run = AsyncMock(
        side_effect=[
            result("required-check"),
            OSError("runner unavailable"),
            result("later-optional-check"),
        ]
    )

    report = await engine.run()

    failed_optional = next(
        check for check in report.checks if check.name == "optional-check"
    )
    required = next(check for check in report.checks if check.name == "required-check")
    later = next(check for check in report.checks if check.name == "later-optional-check")
    assert failed_optional.passed is False
    assert failed_optional.mandatory is False
    assert failed_optional.exit_code == 127
    assert failed_optional.stderr == "failed to start command (OSError): runner unavailable"
    assert required.passed is True
    assert required.mandatory is True
    assert later.passed is True
    assert report.passed is True
    assert engine.runner.run.await_count == 3

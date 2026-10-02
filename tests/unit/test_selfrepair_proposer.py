"""Tests for the self-repair proposer.

The property under test is restraint. A proposer that can emit a proposal without
a real passing test run is worse than no proposer, because downstream it is
treated as evidence. So most of these tests are about what it *refuses* to do.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from app.selfrepair.proposer import (
    CandidateFix,
    GitSelfRepairProposer,
    TestRun,
)

BUGGY = '''\
def add(a, b):
    return a - b
'''

FIXED = '''\
def add(a, b):
    return a + b
'''

GOOD_TEST = '''\
from calc import add


def test_add():
    assert add(1, 2) == 3
'''

BAD_TEST = '''\
from calc import add


def test_add():
    assert add(1, 2) == 999
'''

#: The command is deliberately a plain assertion script rather than pytest: these
#: tests must not depend on a plugin stack that varies by machine.
PY = sys.executable


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True, timeout=60
    )
    return proc.stdout.strip()


def _build(tmp_path: Path, source: str = BUGGY, test: str = GOOD_TEST) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "t@localhost")
    _git(root, "config", "user.name", "T")
    (root / "calc.py").write_text(source, encoding="utf-8")
    (root / "test_calc.py").write_text(test, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init")
    return root, _git(root, "rev-parse", "HEAD")


#: This machine's Application Control policy blocks the pyarrow DLL, so pytest
#: cannot autoload installed plugins. Local environment quirk, not product code.
TEST_ENV = {
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    "PYTEST_ADDOPTS": "-p no:cacheprovider",
}


def _runner() -> str:
    """A real command that executes the tests and exits non-zero on failure.

    Importing the module would not do: it would pass whatever the code did, which
    is exactly the mistake this whole module exists to prevent.
    """
    return f'"{PY}" -m pytest test_calc.py -q'


def _candidate(**kw) -> CandidateFix:
    defaults = dict(
        target_file="calc.py",
        original_snippet="    return a - b\n",
        replacement_snippet="    return a + b\n",
        rationale="add subtracts",
    )
    defaults.update(kw)
    return CandidateFix(**defaults)


@pytest.fixture
def proposer() -> GitSelfRepairProposer:
    return GitSelfRepairProposer(timeout=120.0)


# ── the happy path, with real evidence ────────────────────────────────────


@pytest.mark.asyncio
async def test_a_real_fix_produces_a_proposal_with_a_real_passing_run(tmp_path, proposer):
    repo, base = _build(tmp_path)
    outcome = await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/add",
        candidate=_candidate(),
        test_command=_runner(),
        env=TEST_ENV,
    )
    assert outcome.fixed is True
    assert outcome.before is not None and outcome.before.passed is False
    assert outcome.after is not None and outcome.after.passed is True
    assert outcome.after.returncode == 0
    assert outcome.reason


@pytest.mark.asyncio
async def test_evidence_carries_the_command_and_pass_flag(tmp_path, proposer):
    repo, base = _build(tmp_path)
    outcome = await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/add",
        candidate=_candidate(),
        test_command=_runner(),
        env=TEST_ENV,
    )
    evidence = outcome.after.as_evidence()
    assert evidence["passed"] is True
    assert evidence["returncode"] == 0
    assert "python" in evidence["command"].lower()
    assert evidence["summary"]


@pytest.mark.asyncio
async def test_transcript_contains_verbatim_output(tmp_path, proposer):
    """The evidence must be the actual run, not a summary of intent."""
    repo, base = _build(tmp_path)
    outcome = await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/add",
        candidate=_candidate(),
        test_command=_runner(),
        env=TEST_ENV,
    )
    transcript = outcome.after.transcript()
    assert "$ " in transcript
    assert "exit=0" in transcript
    assert "passed=True" in transcript


# ── refusals ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_proposal_when_the_candidate_does_not_fix_the_test(tmp_path, proposer):
    repo, base = _build(tmp_path)
    outcome = await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/wrong",
        candidate=_candidate(replacement_snippet="    return a * b\n"),
        test_command=_runner(),
        env=TEST_ENV,
    )
    assert outcome.fixed is False
    assert "still fails" in outcome.reason
    assert outcome.after is not None and outcome.after.passed is False


@pytest.mark.asyncio
async def test_no_proposal_when_nothing_was_broken(tmp_path, proposer):
    repo, base = _build(tmp_path, source=FIXED)
    outcome = await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/nothing",
        candidate=_candidate(),
        test_command=_runner(),
        env=TEST_ENV,
    )
    assert outcome.fixed is False
    assert "already passed" in outcome.reason


@pytest.mark.asyncio
async def test_no_proposal_when_the_snippet_is_absent(tmp_path, proposer):
    repo, base = _build(tmp_path)
    outcome = await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/absent",
        candidate=_candidate(original_snippet="    return a * b\n"),
        test_command=_runner(),
        env=TEST_ENV,
    )
    assert outcome.fixed is False
    assert "not present" in outcome.reason


@pytest.mark.asyncio
async def test_no_proposal_when_the_snippet_is_ambiguous(tmp_path, proposer):
    """Two identical lines: refuse rather than guess which one was meant."""
    repo, base = _build(
        tmp_path,
        source="def add(a, b):\n    return a - b\n\n\ndef sub(a, b):\n    return a - b\n",
    )
    outcome = await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/ambiguous",
        candidate=_candidate(),
        test_command=_runner(),
        env=TEST_ENV,
    )
    assert outcome.fixed is False
    assert "times" in outcome.reason


@pytest.mark.asyncio
async def test_a_missing_file_is_an_error_not_a_proposal(tmp_path, proposer):
    repo, base = _build(tmp_path)
    with pytest.raises(FileNotFoundError):
        await proposer.propose(
            repo_path=str(repo),
            base_commit=base,
            branch="repair/missing",
            candidate=_candidate(target_file="nope.py"),
            test_command=_runner(),
        )


@pytest.mark.asyncio
async def test_a_non_repository_is_rejected(tmp_path, proposer):
    with pytest.raises(ValueError, match="not a git repository"):
        await proposer.propose(
            repo_path=str(tmp_path),
            base_commit="HEAD",
            branch="repair/x",
            candidate=_candidate(),
            test_command=_runner(),
        )


# ── the proposer must not apply the fix ───────────────────────────────────


@pytest.mark.asyncio
async def test_the_working_tree_is_handed_back_unchanged(tmp_path, proposer):
    """Forge proposes; the gate applies. Nothing may be written before approval."""
    repo, base = _build(tmp_path)
    await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/add",
        candidate=_candidate(),
        test_command=_runner(),
        env=TEST_ENV,
    )
    assert (repo / "calc.py").read_text(encoding="utf-8") == BUGGY
    assert _git(repo, "branch", "--list", "repair/*") == ""
    assert _git(repo, "status", "--porcelain") == ""


@pytest.mark.asyncio
async def test_a_failed_attempt_also_leaves_nothing_behind(tmp_path, proposer):
    repo, base = _build(tmp_path)
    await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/wrong",
        candidate=_candidate(replacement_snippet="    return a * b\n"),
        test_command=_runner(),
        env=TEST_ENV,
    )
    assert (repo / "calc.py").read_text(encoding="utf-8") == BUGGY
    assert _git(repo, "branch", "--list", "repair/*") == ""
    assert _git(repo, "status", "--porcelain") == ""


@pytest.mark.asyncio
async def test_keep_branch_retains_the_verified_change_for_inspection(tmp_path, proposer):
    repo, base = _build(tmp_path)
    outcome = await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/keep",
        candidate=_candidate(),
        test_command=_runner(),
        keep_branch=True,
    )
    assert outcome.fixed is True
    assert _git(repo, "branch", "--list", "repair/*") != ""


# ── the wire payload ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_request_carries_the_real_repository_and_evidence(tmp_path, proposer):
    repo, base = _build(tmp_path)
    outcome = await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/add",
        candidate=_candidate(),
        test_command=_runner(),
        env=TEST_ENV,
    )
    request = outcome.to_request(str(repo))
    assert request.repo_path == str(Path(repo).resolve())
    assert request.base_commit == base
    assert request.branch == "repair/add"
    assert request.proposed_by == "forge"
    assert request.test_evidence["passed"] is True


@pytest.mark.asyncio
async def test_a_failed_outcome_cannot_produce_a_request(tmp_path, proposer):
    repo, base = _build(tmp_path)
    outcome = await proposer.propose(
        repo_path=str(repo),
        base_commit=base,
        branch="repair/wrong",
        candidate=_candidate(replacement_snippet="    return a * b\n"),
        test_command=_runner(),
        env=TEST_ENV,
    )
    with pytest.raises(RuntimeError, match="refusing to emit a proposal"):
        outcome.to_request(str(repo))


def test_evidence_from_a_failing_run_is_never_marked_passing():
    """The evidence helper must not launder a failure into a pass."""
    run = TestRun(
        command="pytest", passed=False, returncode=1, stdout="", stderr="", duration_ms=5
    )
    assert run.as_evidence()["passed"] is False


def test_outcome_summary_reports_a_pass_flag():
    run = TestRun(
        command="pytest", passed=True, returncode=0, stdout="1 passed", stderr="", duration_ms=5
    )
    assert run.as_evidence()["summary"] == "1 passed"

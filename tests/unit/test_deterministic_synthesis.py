"""
Regression tests for deterministic project synthesis.

The synthesiser is what lets the agent build working software when no model
provider is reachable. Every case here is a real generated project: the code must
compile, the project's own test suite must pass, and the features the goal asked
for must actually be present. No mocks -- the generated files are written to a
real temp directory and executed with a real interpreter.
"""

from __future__ import annotations

import contextlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from app.agents.synthesis import (
    ProjectKind,
    _safe_module_name,
    parse_goal,
    synthesize_files_for_goal,
    synthesize_project,
)

# A spread of goals covering every project kind the synthesiser emits.
CASES: list[tuple[str, ProjectKind, list[str]]] = [
    (
        "Create a Python CLI note-taking app with add, list and delete commands "
        "storing notes in a local JSON file",
        ProjectKind.CLI,
        ["add", "list", "delete"],
    ),
    (
        "Build a command-line todo manager in Python with add, complete, list and "
        "clear commands",
        ProjectKind.CLI,
        ["add", "complete", "list", "clear"],
    ),
    (
        "Create a Python CLI password generator with length and complexity options",
        ProjectKind.CLI,
        ["add"],
    ),
    (
        "Create a FastAPI REST API for a todo list with create, read, update and "
        "delete endpoints",
        ProjectKind.API,
        ["add", "list", "delete", "update"],
    ),
    (
        "Build a REST API for a bookstore inventory with CRUD operations using FastAPI",
        ProjectKind.API,
        ["add", "list", "delete"],
    ),
    (
        "Create a Python script that renames all files in a directory to lowercase",
        ProjectKind.SCRIPT,
        ["rename"],
    ),
    (
        "Create a Python script that converts a JSON file to CSV",
        ProjectKind.SCRIPT,
        ["convert"],
    ),
    (
        "Create a Python string utility library with reverse, palindrome and word "
        "count functions",
        ProjectKind.LIBRARY,
        [],
    ),
    (
        "Build a Python statistics library with mean, median and mode functions",
        ProjectKind.LIBRARY,
        [],
    ),
    (
        "Build a landing page website for a coffee shop with a menu section",
        ProjectKind.WEBSITE,
        [],
    ),
]


@pytest.mark.parametrize(
    "goal,kind,commands", CASES, ids=[c[0][:28] for c in CASES]
)
def test_goal_is_classified(goal: str, kind: ProjectKind, commands: list[str]):
    spec = parse_goal(goal)
    assert spec.kind is kind, f"{spec.kind} != {kind}"
    for cmd in commands:
        assert cmd in spec.commands, f"command {cmd!r} not detected in {spec.commands}"


@pytest.mark.parametrize(
    "goal,kind,commands", CASES, ids=[c[0][:28] for c in CASES]
)
def test_generated_project_compiles(goal: str, kind: ProjectKind, commands: list[str]):
    files = synthesize_project(goal)
    assert files, "synthesis produced nothing"
    if kind is ProjectKind.WEBSITE:
        # A website is HTML/CSS/JS; assert the real assets, not Python.
        assert "index.html" in files, sorted(files)
        assert "<!DOCTYPE html>" in files["index.html"]
        assert len(files["index.html"]) > 2000
        return
    py = {n: c for n, c in files.items() if n.endswith(".py")}
    assert py, f"no Python generated for a {kind.value} project"
    for name, content in py.items():
        compile(content, name, "exec")


@pytest.mark.parametrize(
    "goal,kind,commands", CASES, ids=[c[0][:28] for c in CASES]
)
def test_generated_tests_pass(goal: str, kind: ProjectKind, commands: list[str]):
    """The project's own test suite must pass against the generated code."""
    files = synthesize_project(goal)
    tests = sorted(n for n in files if re.match(r"test_.*\.py$", n))
    if not tests:
        pytest.skip(f"{kind.value} project has no test suite")
    with tempfile_project(files) as root:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider",
             *tests],
            cwd=str(root), capture_output=True, text=True, timeout=300,
        )
    assert proc.returncode == 0, (
        f"generated tests failed:\n{proc.stdout[-2500:]}\n{proc.stderr[-800:]}"
    )


def test_cli_implements_every_requested_command():
    goal = (
        "Create a Python CLI note-taking app with add, list and delete commands "
        "storing notes in a local JSON file"
    )
    source = synthesize_project(goal)["main.py"]
    for cmd in ("add", "list", "delete"):
        assert f'"{cmd}"' in source, f"subcommand {cmd} missing from the generated CLI"


def test_generated_module_never_shadows_stdlib():
    """A module named string.py breaks pytest itself with an ImportError."""
    for name in ("string", "json", "os", "test", "typing"):
        assert _safe_module_name(name) != name
        assert _safe_module_name(name).endswith("_utils")


def test_empty_and_hostile_goals_do_not_crash():
    for goal in ("", "   ", "!@#$%", "\x00\x01", "a" * 5000, "app"):
        files = synthesize_project(goal)
        assert isinstance(files, dict)
        for name, content in files.items():
            if name.endswith(".py"):
                compile(content, name, "exec")


def test_unknown_goal_still_yields_a_runnable_project():
    files = synthesize_project("zzz qqq")
    assert files
    assert any(n.endswith(".py") for n in files)


def test_manifest_is_respected():
    goal = "Create a Python CLI note-taking app with add and list commands"
    files = synthesize_files_for_goal(goal, manifest=["main.py"])
    assert "main.py" in files
    # The manifest's names are kept and filled from the generators.
    assert all(n == "main.py" or n.startswith("test_") or n == "requirements.txt"
               for n in files)


def test_manifest_names_never_strip_the_implementation():
    """A manifest asking for main.py must not drop the module that was built.

    The manifest is written by the architect and names files generically; a
    script that renames files is delivered as path.py. Matching on the manifest
    name alone kept the README and the test suite while silently dropping
    path.py, so the user got tests for a module that was never written -- and
    every script/library goal in the real campaign failed this way.
    """
    goal = "Create a Python script that renames all files in a directory to lowercase"
    files = synthesize_files_for_goal(
        goal, manifest=["main.py", "test_main.py", "README.md"], requirements=["rename"]
    )
    assert files, "synthesis produced nothing"
    modules = [n for n in files if n.endswith(".py") and not n.startswith("test_")]
    assert modules, f"the implementation module was dropped: {sorted(files)}"
    assert "test_path.py" in files
    # The unsatisfiable manifest names stay absent rather than being faked.
    assert "main.py" not in files


def test_every_project_kind_keeps_its_implementation_under_a_manifest():
    goals = [
        "Create a Python CLI habit tracker with add and list commands",
        "Create a FastAPI REST API for user registration with login",
        "Create a Python script that renames files in a directory",
        "Create a Python library for string manipulation utilities",
    ]
    for goal in goals:
        files = synthesize_files_for_goal(
            goal, manifest=["main.py", "test_main.py"], requirements=[]
        )
        modules = [n for n in files if n.endswith(".py") and not n.startswith("test_")]
        assert modules, f"{goal!r} lost its implementation: {sorted(files)}"
        tests = [n for n in files if n.startswith("test_")]
        assert tests, f"{goal!r} lost its test suite: {sorted(files)}"


def test_readme_matches_the_project_kind():
    website = synthesize_project("Build a landing page website for a coffee shop")
    assert "index.html" in website["README.md"]
    assert "python main.py --help" not in website["README.md"]

    cli = synthesize_project("Create a Python CLI note-taking app with add and list")
    assert "python main.py --help" in cli["README.md"]


@contextlib.contextmanager
def tempfile_project(files: dict[str, str]):
    with tempfile.TemporaryDirectory(prefix="forge_synth_") as d:
        root = Path(d)
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        yield root

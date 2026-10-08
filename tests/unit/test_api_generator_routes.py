"""
Regression tests for two real bugs in the deterministic Web API generator
(`_api_main` / `_api_tests` in app/agents/synthesis.py), found by actually
generating a project and running the resulting FastAPI app -- not by reading
the source or relying on the generated project's own (also-buggy) test
suite, which could not catch either bug because it was generated from the
same incorrect assumptions as the code it tested.

Finding 14 -- inconsistent singular/plural resource paths:
    Collection routes were mounted on the plural form (`POST /items`,
    `GET /items`) while every item-level route used the singular form
    (`GET /item/{id}`, `PUT /item/{id}`, `DELETE /item/{id}`). Any client
    assuming the universal REST convention of one consistent base path
    (`/items` and `/items/{id}`) got a 404 on every by-id operation. Live
    repro: POST /books created record id=1, GET /books/1 (plural) 404'd,
    only GET /book/1 (singular) worked.

Finding 15 -- the search route was completely unreachable:
    The literal route `/{plural}/search` was registered *after* the
    parameterized route `/{plural}/{id}:int` on the same prefix. FastAPI
    matches routes in registration order and does not fall through to a
    later route when an earlier one matches the URL shape but fails
    parameter validation, so a real request to `/items/search` matched
    `/items/{item_id}` first, failed int-parsing on the literal string
    "search", and returned 422 from the wrong handler -- the search
    endpoint existed in the code and the OpenAPI schema and could never be
    reached. Live repro confirmed the exact 422 `int_parsing` error.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.agents.synthesis import _detect_commands, _tokens, parse_goal, synthesize_project


def _load_generated_api(goal: str) -> TestClient:
    """Generate a Web API project for `goal` and actually import/run it as a
    real module (the same way a user would run `python main.py`), not an
    isolated `exec()` namespace -- Pydantic's forward-ref resolution (needed
    because the generated code uses `from __future__ import annotations`)
    requires the module to be registered in `sys.modules`."""
    files = synthesize_project(goal)
    tmpdir = Path(tempfile.mkdtemp(prefix="forge_api_gen_test_"))
    (tmpdir / "main.py").write_text(files["main.py"])

    mod_name = f"forge_generated_api_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, tmpdir / "main.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return TestClient(module.app)


def test_crud_keyword_implies_update():
    """Finding 16: the literal word "CRUD" -- the single most common way a
    real user phrases this request -- did not imply "update" because no
    individual COMMAND_SIGNALS entry matches the acronym itself. A goal that
    explicitly says "with CRUD endpoints" must produce all four operations,
    not just the three whose names happen to appear in COMMAND_SIGNALS."""
    goal = "Build a REST API for managing books with CRUD endpoints using FastAPI"
    commands = _detect_commands(_tokens(goal))
    assert "update" in commands, (
        f"goal explicitly asks for CRUD but commands={commands} has no update"
    )
    for expected in ("add", "list", "delete"):
        assert expected in commands


def test_generated_crud_api_actually_has_a_working_update_route():
    goal = "Build a REST API for managing books with CRUD endpoints using FastAPI"
    spec = parse_goal(goal)
    plural = spec.entity_plural
    client = _load_generated_api(goal)

    created = client.post(
        f"/{plural}", json={"title": "Dune", "author": "Frank Herbert", "year": 1965, "isbn": "1"}
    )
    assert created.status_code == 201, created.text
    item_id = created.json()["id"]

    r = client.put(
        f"/{plural}/{item_id}",
        json={"title": "Dune Messiah", "author": "Frank Herbert", "year": 1969, "isbn": "2"},
    )
    assert r.status_code == 200, (
        f"CRUD goal produced no working update route (got {r.status_code}). Body: {r.text}"
    )
    assert r.json()["title"] == "Dune Messiah"


def test_generated_api_uses_consistent_plural_paths():
    goal = "Build a REST API for managing books with CRUD endpoints using FastAPI"
    spec = parse_goal(goal)
    plural = spec.entity_plural

    client = _load_generated_api(goal)

    created = client.post(
        f"/{plural}", json={"title": "Dune", "author": "Frank Herbert", "year": 1965, "isbn": "1"}
    )
    assert created.status_code == 201, created.text
    item_id = created.json()["id"]

    # The actual regression: the plural-prefixed item route must work, not
    # just the singular one.
    r = client.get(f"/{plural}/{item_id}")
    assert r.status_code == 200, (
        f"GET /{plural}/{{id}} 404'd -- item routes are not using the same "
        f"prefix as the collection routes. Body: {r.text}"
    )
    assert r.json()["id"] == item_id

    r = client.put(
        f"/{plural}/{item_id}",
        json={"title": "Dune Messiah", "author": "Frank Herbert", "year": 1969, "isbn": "2"},
    )
    assert r.status_code == 200, r.text

    r = client.delete(f"/{plural}/{item_id}")
    assert r.status_code == 204, r.text


def test_generated_api_search_route_is_reachable():
    goal = (
        "Build a REST API for managing products with CRUD and search endpoints "
        "using FastAPI, allow searching products"
    )
    spec = parse_goal(goal)
    assert "search" in spec.commands, "test setup assumption failed: goal must imply search"
    plural = spec.entity_plural

    client = _load_generated_api(goal)

    created = client.post(f"/{plural}", json={"name": "widget", "value": "42"})
    assert created.status_code == 201, created.text

    # The actual regression: this used to 422 with a path-parameter
    # int-parsing error because /{plural}/{id} was registered first and
    # structurally matched "search" as the id.
    r = client.get(f"/{plural}/search", params={"q": "widget"})
    assert r.status_code == 200, (
        f"GET /{plural}/search did not reach the search handler -- it is "
        f"shadowed by the /{plural}/{{id}} route. Body: {r.text}"
    )
    results = r.json()
    assert isinstance(results, list)
    assert any(item.get("name") == "widget" for item in results)

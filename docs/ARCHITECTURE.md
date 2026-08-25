# FORGE System Architecture

## Overview
**Project FORGE** is an Autonomous Software Engineering Engine designed to translate high-level software goals into verifiable, production-ready software artifacts through autonomous decomposition, generation, testing, and self-healing recovery.

---

## Core Components

```
FORGE/
├── app/
│   ├── main.py                     # FastAPI application setup and lifecycle management
│   ├── api/                        # HTTP REST API routers (/health, /projects)
│   ├── core/                       # Settings, Configuration, and Structured Logging
│   ├── agents/                     # Specialized agent personas and execution loops
│   ├── planning/                   # Goal decomposition, task dependency graphs
│   ├── execution/                  # Code generation, tool execution, terminal interactions
│   ├── verification/               # Test runner, static analysis, boundary verifiers
│   ├── recovery/                   # Self-healing, rollback, error mitigation
│   ├── memory/                     # SQLite persistence, StateStore, TaskGraph, Checkpoints
│   └── providers/                  # BaseModelProvider abstraction and DirectProvider implementation
├── data/                           # SQLite database storage (forge.db)
├── workspaces/                     # Isolated project execution environments
├── artifacts/                      # Final generated builds, logs, and outputs
└── tests/                          # Multi-tiered automated test suite
```

---

## 1. Database & State Layer (`app/memory/`)

- **SQLite Backend**: Using `aiosqlite` with Write-Ahead Logging (`WAL`) mode and foreign keys enabled.
- **`ProjectWorkspace`**: Entity representing a software project and its dedicated filesystem sandbox.
- **`TaskGraph`**: Directed acyclic graph (DAG) representing goal decomposition into distinct `TaskNode` units with dependency constraints.
- **`Checkpoint`**: Step-by-step state snapshot allowing rollbacks and post-mortem auditing.
- **`StateStore`**: Asynchronous persistence service managing projects, graph transitions, and checkpoints.

---

## 2. Model Providers (`app/providers/`)

- **`BaseModelProvider` (ABC)**:
  - `generate()`: Single-turn or multi-turn text completions.
  - `stream()`: Asynchronous token generator.
  - `structured_output()`: Schema-driven JSON extraction validated via Pydantic.
  - `estimate_usage()`: Token and cost estimation.
  - `capabilities()`: Provider feature set and context window metadata.
  - `health()`: Operational status and latency probing.
- **`DirectProvider`**:
  - Standalone implementation capable of direct text generation, streaming token emission, mock synthesis, and Pydantic validation.

---

## 3. FastAPI Service & Workspaces (`app/main.py`, `app/api/`)

- **`GET /health`**: Health status, database connectivity, and active provider telemetry.
- **`POST /projects`**: Provisions an isolated workspace inside `workspaces/<project_id>`, creates standard project subdirectories (`src/`, `tests/`, `.forge`), and persists metadata in SQLite.
- **`GET /projects` & `GET /projects/{id}`**: Workspace queries and retrieval.

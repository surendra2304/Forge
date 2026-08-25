# Project FORGE 🔨

**FORGE** is an **Autonomous Software Engineering Engine** that transforms high-level software goals into verified, packaged, and production-ready software artifacts through autonomous planning, execution, objective verification, and self-repair.

FORGE operates as a **100% independent, standalone tool** (via CLI and local REST API) requiring no external ecosystem dependencies.

---

## 🏗️ Repository Architecture

```text
FORGE/
├── app/
│   ├── main.py                     # FastAPI application entry point
│   ├── cli.py                      # Standalone Rich CLI MVP (forge build, status, logs)
│   ├── api/                        # REST API endpoints (tasks, timeline, artifacts, capabilities)
│   ├── core/                       # Orchestrator, Workspace Manager, Events & Telemetry
│   ├── agents/                     # 10 Specialist Agent Roles (Planner, Architect, Dev, Tester, etc.)
│   ├── planning/                   # 8-Stage Hierarchical Tree & Executable Task DAG
│   ├── execution/                  # Sandboxed Tools (Filesystem, Terminal, Process, Git, Delivery)
│   ├── verification/               # Evidence Battery (Build, Lint, Pytest, Playwright Browser)
│   ├── recovery/                   # Self-Repair, Anti-Loop Controller, Failure Classifier
│   ├── memory/                     # SQLite WAL StateStore & 8-State Task Lifecycle
│   └── providers/                  # BaseModelProvider abstraction & DirectProvider
├── data/                           # SQLite database storage (forge.db)
├── workspaces/                     # Isolated project sandboxes (workspaces/task_<id>/)
├── artifacts/                      # Completion reports, verification manifests, screenshots
├── tests/
│   ├── unit/                       # Unit tests (agents, lifecycle, providers, recovery, timeline)
│   ├── integration/                # API and multi-component tests
│   └── golden/                     # 3 Golden Regression Benchmarks (CLI, FastAPI, Static Web)
├── docs/
│   └── architecture.md             # System architecture and design documentation
├── .agents/rules/                  # Permanent engineering rules & diary governance
├── diary/                          # Day-wise engineering development chronicles
├── FORGE_DIARY.md                  # Master consolidated development diary
├── FORGE_DIARY_SPEC.md             # Diary specification standard
├── pyproject.toml                  # Modern Python packaging configuration
└── README.md                       # Project overview and documentation
```

---

## ⚡ Quick Start

### 1. Installation
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Running the Standalone CLI
```bash
# Autonomously build a software project from specification
forge build "Create a robust CLI Todo utility with JSON persistence"

# Inspect task status, timeline, or logs
forge status <task_id>
forge logs <task_id>
forge inspect <task_id>
```

### 3. Running the REST API Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Running the Complete Test Suite
```bash
pytest -v tests/
```

---

## 🛡️ Core Verification & Isolation Principles

- **Objective Evidence Over Model Confidence**: Tasks are verified via AST build checks, Ruff linting, Pytest test suites, and Playwright headless browser checks.
- **Strict Sandbox Isolation**: All operations occur within `workspaces/task_<id>/`.
- **Parallel DAG Scheduling**: Concurrent tasks run in parallel waves via `asyncio.gather`.
- **Anti-Loop Self-Repair**: Caps retries (max 3) and deduplicates patches via SHA256 hashes to prevent infinite repair loops.
- **Autonomous Delivery Packaging**: Every completed task generates `completion_report.json`, `COMPLETION_REPORT.md`, and creates a signed git release tag (`v1.0-forge-delivery`).

---

## 📖 Development Diary

FORGE adheres to a strict, day-wise development chronicle governance model:
- **[FORGE_DIARY.md](FORGE_DIARY.md)**: Consolidated master diary and navigation index.
- **[FORGE_DIARY_SPEC.md](FORGE_DIARY_SPEC.md)**: Specification and structural rules.
- **[diary/](diary/)**: Date-stamped chronicle entries.

# Project FORGE 🔨

**FORGE** is an **Autonomous Software Engineering Engine** that transforms high-level software goals into verified, packaged, and production-ready software artifacts through autonomous planning, execution, verification, and self-repair.

FORGE is designed to operate both as an independent autonomous CLI/API and as the core software engineering delegation engine for **FRIDAY** and the **AI Universe**.

---

## 🏗️ Repository Architecture

```text
FORGE/
├── app/
│   ├── main.py                     # FastAPI application entry point
│   ├── cli.py                      # Standalone Rich CLI MVP (forge build, status, logs)
│   ├── api/                        # REST API, Auth, Permission Boundaries, FRIDAY routes
│   ├── core/                       # Orchestrator, Workspace Manager, Events & Telemetry
│   ├── agents/                     # 10 Specialist Agent Roles (Planner, Architect, Dev, Tester, etc.)
│   ├── planning/                   # 8-Stage Hierarchical Tree & Executable DAG
│   ├── execution/                  # Sandboxed Tools (Filesystem, Terminal, Process, Git, Delivery)
│   ├── verification/               # Evidence Battery (Build, Lint, Pytest, Playwright Browser)
│   ├── recovery/                   # Self-Repair, Anti-Loop Controller, Failure Classifier
│   ├── memory/                     # SQLite WAL StateStore & 8-State Task Lifecycle
│   └── providers/                  # DirectProvider & AIUniverseProvider (Fast, Review, Debate)
├── data/                           # SQLite database storage (forge.db)
├── workspaces/                     # Isolated project sandboxes (workspaces/task_<id>/)
├── artifacts/                      # Completion reports, verification manifests, screenshots
├── tests/
│   ├── unit/                       # Unit tests (agents, lifecycle, providers, recovery, timeline)
│   ├── integration/                # API and multi-component tests
│   └── golden/                     # 3 Golden Regression Benchmarks (CLI, FastAPI, Static Web)
├── docs/
│   └── architecture.md             # System architecture & FRIDAY integration spec
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

### 2. Configuration
Copy the environment template:
```bash
cp .env.example .env
```

### 3. Running the Standalone CLI
```bash
# Autonomously build a software project from specification
forge build "Create a robust CLI Todo utility with JSON persistence"

# Inspect task status, timeline, or logs
forge status <task_id>
forge logs <task_id>
forge inspect <task_id>
```

### 4. Running the REST API Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Running the Complete Test Suite
```bash
pytest -v tests/
```

---

## 🤝 FRIDAY Ecosystem Integration Contract

FORGE exposes a secure, boundary-enforced contract for FRIDAY assistant delegation:

- **`POST /friday/delegate`**: Authenticated task delegation (`FRIDAYTaskRequest` $\rightarrow$ `FORGETaskResult`).
- **`GET /friday/tasks/{task_id}/result`**: Delivers structured manifests, test evidence, screenshots, and release tags.
- **`GET /tasks/{task_id}/timeline`**: Real-time chronological event stream with automatic secret redaction.

---

## 🛡️ Security & Sandbox Boundaries

- **Sandbox Isolation**: All file operations and shell commands run exclusively inside `workspaces/task_<id>/`.
- **Permission Boundary**: Requests exceeding the sandbox without explicit user authorization return `HTTP 403 Forbidden`.
- **API Key Security**: Endpoints authenticate via `X-API-Key` or `Authorization: Bearer <key>`.
- **Secret Redaction**: API keys and tokens are automatically masked across all logs and telemetry streams.

---

## 📖 Development Diary

FORGE adheres to a strict, day-wise development chronicle governance model:
- **[FORGE_DIARY.md](FORGE_DIARY.md)**: Consolidated master diary and navigation index.
- **[FORGE_DIARY_SPEC.md](FORGE_DIARY_SPEC.md)**: Specification and structural rules.
- **[diary/](diary/)**: Date-stamped chronicle entries.

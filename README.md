# Project FORGE 🔨

**FORGE** is an **Autonomous Software Engineering Engine** that takes a high-level software goal and turns it into an actual, verified software artifact through autonomous planning, execution, verification, and recovery.

---

## 🏗️ Repository Architecture

```text
FORGE/
├── app/
│   ├── main.py                     # FastAPI application entry point
│   ├── api/                        # HTTP REST API endpoints (/health, /projects)
│   ├── core/                       # App configuration (pydantic-settings) & logging
│   ├── agents/                     # Specialized agent personas and workflows
│   ├── planning/                   # Goal decomposition & task graph synthesis
│   ├── execution/                  # Code generation & sandboxed execution
│   ├── verification/               # Automated test runners & correctness checks
│   ├── recovery/                   # Self-healing, rollback & error mitigation
│   ├── memory/                     # SQLite persistence (StateStore, TaskGraph, Checkpoints)
│   └── providers/                  # BaseModelProvider abstraction & DirectProvider
├── data/                           # SQLite database storage (forge.db)
├── workspaces/                     # Isolated project sandboxes
├── artifacts/                      # Generated builds, logs, and artifacts
├── tests/
│   ├── unit/                       # Unit tests (providers, memory, models)
│   ├── integration/                # API and multi-component tests
│   ├── execution/                  # Sandbox and execution tests
│   ├── verification/               # Verification engine tests
│   ├── security/                   # Boundary and permission tests
│   └── golden/                     # Benchmark and evaluation suites
├── docs/                           # Architecture and design documentation
├── .agents/rules/                  # Permanent engineering rules & memory policies
├── diary/                          # Day-wise engineering development chronicles
├── scripts/                        # Management and automation scripts
├── .env.example                    # Environment configuration template
├── .gitignore                      # Git ignore rules
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

### 3. Running the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Running Tests
```bash
pytest -v tests/
```

---

## 🔌 Core API Endpoints

- **`GET /health`**: Health status, database connectivity, and provider telemetry.
- **`POST /projects`**: Provision a new isolated project workspace.
- **`GET /projects`**: List all project workspaces.
- **`GET /projects/{project_id}`**: Retrieve project details by ID.

---

## 📖 Development Diary

Forge adheres to a strict, day-wise development chronicle governance model:
- **[FORGE_DIARY.md](FORGE_DIARY.md)**: Consolidated master diary and navigation index.
- **[FORGE_DIARY_SPEC.md](FORGE_DIARY_SPEC.md)**: Specification and structural rules.
- **[diary/](diary/)**: Date-stamped chronicle entries.

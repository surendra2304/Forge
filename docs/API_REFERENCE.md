# FORGE — FRIDAY Management API Reference

Project FORGE exposes a rich REST and real-time WebSocket API designed for automated orchestration and supervision by Project FRIDAY, as well as developer consumption.

---

## Authentication

All REST endpoints and WebSocket channels support API Key authentication:
- **Header:** `X-FRIDAY-API-Key: <api_key>` or `X-API-Key: <api_key>`
- **Query Parameter (WebSockets):** `?api_key=<api_key>`

---

## REST Endpoints

### 1. Task Management (`/api/tasks`)

#### Submit Task
- **Endpoint:** `POST /api/tasks`
- **Description:** Submit a new high-level engineering goal for autonomous decomposition, synthesis, and verification.
- **Request Body:**
  ```json
  {
    "goal": "Build a responsive static personal portfolio website with dark mode",
    "requirements": ["Responsive layout", "Hero section", "Dark mode toggle"],
    "mode": "autonomous",
    "max_budget": 10.0,
    "task_metadata": {
      "source": "friday",
      "priority": "high",
      "deadline": "2026-08-28T00:00:00Z",
      "tags": ["frontend", "portfolio"]
    }
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": "task0127082026190000",
    "goal": "Build a responsive static personal portfolio website with dark mode",
    "requirements": ["Responsive layout", "Hero section", "Dark mode toggle"],
    "mode": "autonomous",
    "workspace_path": "workspaces/task0127082026190000",
    "max_budget": 10.0,
    "budget_consumed": 0.0,
    "state": "PENDING",
    "progress_percentage": 0,
    "metadata": {
      "source": "friday",
      "priority": "high",
      "tags": ["frontend", "portfolio"],
      "archived": false
    },
    "created_at": "2026-08-27T19:00:00Z",
    "updated_at": "2026-08-27T19:00:00Z"
  }
  ```

#### List Tasks
- **Endpoint:** `GET /api/tasks`
- **Query Parameters:**
  - `status` (*string*, optional): Filter by `PENDING`, `READY`, `RUNNING`, `VERIFYING`, `COMPLETED`, `FAILED`, `CANCELLED`, `BLOCKED`.
  - `limit` (*integer*, default: 50): Max tasks to return.
  - `since_timestamp` (*string*, optional): ISO timestamp filter.
  - `include_archived` (*boolean*, default: false): Include soft-archived tasks.
- **Response (200 OK):**
  ```json
  [
    {
      "id": "task0127082026190000",
      "goal": "Build a responsive static personal portfolio website with dark mode",
      "state": "COMPLETED",
      "progress_percentage": 100,
      "project_type": "website",
      "priority": "high",
      "created_at": "2026-08-27T19:00:00Z",
      "updated_at": "2026-08-27T19:00:25Z",
      "archived": false
    }
  ]
  ```

#### Get Task Details & Dynamic ETA
- **Endpoint:** `GET /api/tasks/{task_id}`
- **Response (200 OK):**
  ```json
  {
    "id": "task0127082026190000",
    "goal": "Build a responsive static personal portfolio website with dark mode",
    "state": "RUNNING",
    "progress_percentage": 65,
    "current_stage": "Verification",
    "estimated_remaining_seconds": 8.5,
    "estimated_completion_at": "2026-08-27T19:00:33Z",
    "workspace_dirs": {
      "root": "workspaces/task0127082026190000",
      "project": "workspaces/task0127082026190000/project",
      "artifacts": "workspaces/task0127082026190000/artifacts",
      "logs": "workspaces/task0127082026190000/logs",
      "state": "workspaces/task0127082026190000/state",
      "cache": "workspaces/task0127082026190000/cache"
    },
    "provenance_summary": "Generated via: AI-Universe (80.0%), Direct (20.0%), Template (0.0%)"
  }
  ```

#### Deep Task Inspection
- **Endpoint:** `GET /api/tasks/{task_id}/inspect`
- **Response (200 OK):**
  ```json
  {
    "task_id": "task0127082026190000",
    "goal": "Build a responsive static personal portfolio website with dark mode",
    "state": "COMPLETED",
    "files_created": [
      {"path": "index.html", "size_bytes": 3420, "lines_count": 92},
      {"path": "style.css", "size_bytes": 4120, "lines_count": 180},
      {"path": "app.js", "size_bytes": 1050, "lines_count": 35}
    ],
    "verification_summary": {
      "all_passed": true,
      "passed_checks": 7,
      "failed_checks": 0
    },
    "dependencies": [],
    "artifacts": ["completion_report.json", "COMPLETION_REPORT.md", "verification_manifest.json"]
  }
  ```

#### Execution Logs
- **Endpoint:** `GET /api/tasks/{task_id}/logs`
- **Query Parameters:** `level` (`DEBUG`, `INFO`, `WARNING`, `ERROR`), `tail_lines` (default 100), `since_timestamp`.
- **Response (200 OK):** Structured logs list with inferred log level.

#### Artifacts & Downloads
- **Endpoint:** `GET /api/tasks/{task_id}/artifacts` — List available deliverables and report files.
- **Endpoint:** `GET /api/tasks/{task_id}/artifacts/{filename}` — Direct file stream download.

#### Cancellation & Soft Archive
- **Endpoint:** `POST /api/tasks/{task_id}/cancel` — Graceful task abort with background process termination.
- **Endpoint:** `DELETE /api/tasks/{task_id}` — Soft-archive task while keeping sandbox files intact.

---

### 2. Analytics & Historical Metrics (`/api/analytics`)

- **`GET /api/analytics/summary`**: High-level execution metrics (total tasks, success rate %, average duration, budget spent).
- **`GET /api/analytics/types`**: Performance, duration, and success rates segmented by project category (`website`, `cli`, `api`, `script`, `fullstack`).
- **`GET /api/analytics/failures`**: Root-cause failure distribution (`fallback_stub`, `verification_failure`, `security_violation`, etc.).

---

## WebSocket Telemetry Streams

### 1. Task-Specific Stream (`/ws/tasks/{task_id}`)
Connect to subscribe to real-time events for a single task:
- `stage.started`, `stage.completed`
- `verification.evidence`
- `task.state_changed`
- `task.completed`, `task.failed`

### 2. Global Stream (`/ws/tasks`)
Connect to receive broadcasts across all active engineering tasks:
- `task.created`
- `task.cancelled`
- State transitions and completion notifications.

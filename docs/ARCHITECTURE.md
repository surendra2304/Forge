# FORGE System Architecture & FRIDAY Ecosystem Integration

Project FORGE is an **Autonomous Software Engineering Engine** engineered to intake high-level software objectives and autonomously synthesize, verify, debug, package, and deliver verified production software artifacts.

---

## 1. High-Level Ecosystem Topology

```text
       +-------------------------------------------------------------+
       |                           FRIDAY                            |
       |       (High-Level Executive Assistant & Project Owner)       |
       +------------------------------+------------------------------+
                                      |
                      POST /friday/delegate (API Key Auth)
                      FRIDAYTaskRequest -> FORGETaskResult
                                      |
                                      v
       +-------------------------------------------------------------+
       |                        FORGE ENGINE                         |
       |                                                             |
       |  +-------------------------------------------------------+  |
       |  |                    Orchestrator                       |  |
       |  |  (Task Analyzer -> 8-Stage Planning DAG -> Scheduler) |  |
       |  +---------------------------+---------------------------+  |
       |                              |                              |
       |             +----------------+----------------+             |
       |             |                                 |             |
       |             v                                 v             |
       |  +-----------------------+       +-----------------------+  |
       |  |   Specialist Agents   |       |  Sandboxed Workspace  |  |
       |  |   (Planner, Architect,|       |  (workspaces/task_id) |  |
       |  |   Developer, Tester,  |       |  - project/           |  |
       |  |   Release Engineer)   |       |  - artifacts/         |  |
       |  +-----------+-----------+       +-----------+-----------+  |
       |              |                               |              |
       |              +---------------+---------------+              |
       |                              |                              |
       |                              v                              |
       |  +-------------------------------------------------------+  |
       |  |           Objective Verification Engine               |  |
       |  |   (AST Build, Ruff Lint, Pytest, Playwright Browser)  |  |
       |  +---------------------------+---------------------------+  |
       |                              |                              |
       |                              v                              |
       |  +-------------------------------------------------------+  |
       |  |            Delivery Packager & Git Tagging            |  |
       |  |  (completion_report.json, COMPLETION_REPORT.md, tag)  |  |
       |  +-------------------------------------------------------+  |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                     AI Universe Swarms                      |
       |    (AIUniverseProvider: FAST | REVIEW | DEBATE Modes)       |
       +-------------------------------------------------------------+
```

---

## 2. FRIDAY Integration Contract

FORGE exposes an authenticated, boundary-enforced contract tailored for FRIDAY delegation:

### Endpoints:
- **`POST /friday/delegate`**: Intakes `FRIDAYTaskRequest`, verifies API Key and sandbox permission scope, provisions workspace, executes parallel DAG waves, and returns `FORGETaskResult`.
- **`GET /friday/tasks/{task_id}/result`**: Retrieves full deliverable manifest for a completed task.
- **`GET /tasks/{task_id}/timeline`**: Returns chronological telemetry stream for external dashboards.

### Correlation ID Propagation:
$$\text{FRIDAY Task ID} \longrightarrow \text{FORGE Task ID} \longrightarrow \text{FORGE Run ID} \longrightarrow \text{Git Release Tag}$$

---

## 3. Security & Permission Boundaries

1. **Workspace Sandbox Isolation**:
   - All file mutations, process spawns, and git commits are strictly confined to `workspaces/task_<id>/`.
   - Host path traversals outside the task directory are blocked with `SandboxViolationError`.
2. **Permission Boundary Enforcement**:
   - Operations requesting `unrestricted`, `modify_personal_files`, or `production_deploy` without explicit user authorization return `403 Forbidden: Permission Denied`.
3. **API Key Authentication**:
   - Requests are authenticated via `X-API-Key` or `Authorization: Bearer <key>` headers against `FORGE_API_KEY`.
4. **Secret Redaction**:
   - `SecretRedactor` automatically masks API keys (`sk-...`, `ghp_...`, `AIza...`), tokens, and credentials from all audit event streams and logs.

---

## 4. Verification & Self-Repair ("Evidence Over Confidence")

FORGE enforces strict objective verification gates:
1. **AST Build Check**: Syntax and AST parse validation.
2. **Static Code Linter**: `ruff check . --select=E,F`.
3. **Pytest Suite Runner**: Test execution and assertion validation.
4. **Runtime Smoke Check**: CLI `--help` or entrypoint execution.
5. **Headless Browser Checker**: Playwright Chromium automation verifying console logs, network errors (4xx/5xx), missing assets, DOM interactivity, and PNG screenshot capture.

If verification fails, `RecoveryEngine` classifies root cause, deduplicates patches with SHA256 hashes, caps retries to 3 per failure class, and applies self-repair fixes.

---

## 5. Multi-Agent Intelligence Adapter (`AIUniverseProvider`)

Connects FORGE to external or simulated multi-agent swarm intelligence:
- **`FAST`**: Single-pass high-speed optimal reasoning.
- **`REVIEW`**: Multi-persona review (`ArchitectPersona`, `SeniorDevPersona`, `JudgeEvaluator`) $\rightarrow$ compare $\rightarrow$ select optimal architecture.
- **`DEBATE`**: Adversarial debate protocol (`ProponentSpecialist`, `AdversaryCritique`, `RebuttalSpecialist`, `ConsensusSynthesizer`) $\rightarrow$ rebuttal-tested consensus with provenance and dissent tracking.

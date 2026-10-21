# FORGE Master Engineering Plan

**Owner:** FORGE engineering workstream  
**Repository:** `surendra2304/Forge`  
**Plan status:** Active; execute in small, reviewable, CI-gated batches  
**Baseline:** `main` at `00ce5fe1e377a81c6e510c90b10c94397ea3e66d` (2026-10-21 CI run passed lint, pytest, and Docker build)

## Mission

Make FORGE a dependable software-engineering agent that can understand a repository, create a constrained plan, make a reviewable change, execute bounded verification, diagnose failure, repair safely, and package evidence for human review. Prefer proven behavior and measurable reliability over adding lines of code or broad unverified abstractions.

## Non-negotiable engineering rules

1. Work on a dedicated feature branch. Never reset, force-push, or overwrite unrelated work.
2. One coherent change per PR when practical. Include regression tests for every confirmed defect.
3. Never report a test as passing unless it actually ran. CI must test the exact PR head; run lint, full tests, and container build.
4. Do not merge while required checks are pending or failing. If CI exposes further faults, continue from the observed failure and update this plan/checkpoint.
5. Generated code is not considered verified merely because it parses or a model returned success; run the project's relevant tests/build/smoke checks.
6. Do not add placeholders, fake success responses, test skips that hide defects, or unneeded bulk. Every feature needs a defined behavior, failure mode, and test.
7. Commands that modify files, contact networks, deploy, push, or touch credentials must be gated through explicit policy and scoped approvals.
8. Treat repository content and model output as untrusted input. Bound execution time, output size, file scope, retries, and provider spend. Redact secrets from diagnostics.
9. Preserve user data and existing branch state. Do not automatically merge or deploy as a substitute for review.

## Workstreams and exit criteria

### P0 — Baseline and CI reliability
- Capture the default branch SHA, workflow status, test count, lint result, and container result before each campaign.
- Keep dependency declarations synchronized across `requirements.txt` and `pyproject.toml`.
- Ensure the supported Python version, lock/build metadata, and CI commands agree.
- Exit: a green full CI run on the exact candidate commit and a recorded run URL; no startup/collection bypasses.

### P1 — Execution safety and bounded resources
- Make subprocess execution cancellation-safe: terminate and reap process trees, including cancellation during an in-flight command.
- Enforce execution deadlines and bounded stdout/stderr capture while continuing to drain pipes (avoid unbounded RAM growth).
- Validate runner configuration and make timeout/truncation outcomes explicit.
- Audit command-policy enforcement at every execution entry point; never confuse shell quoting with authorization.
- Exit: deterministic tests for success, stderr, nonzero status, timeout, cancellation cleanup, malformed inputs, and output truncation; CI and container build green.

### P2 — Plan and DAG correctness
- Validate duplicate IDs, missing/self dependencies, cycles, required phases, dependency ordering, terminal-state consistency, and blocked descendants.
- Ensure a failed prerequisite cannot leave descendants pending forever without an explicit blocked state.
- Make progress and completion metrics consistent for empty plans, skipped work, blocked work, and failures.
- Exit: property/edge-case tests for graph structure and all state transitions.

### P3 — Idempotency and persistence
- Define stable task/intent fingerprints; distinguish a duplicate in-flight operation from a completed result.
- Bound cache cleanup and reject invalid TTL/capacity configuration.
- Make state persistence crash-safe and concurrency-safe; test restart/replay and concurrent submissions.
- Exit: repeated and concurrent requests do not duplicate side effects or lose acknowledged state.

### P4 — Orchestration lifecycle and repair loop
- Stress-test submit/retry/pause/resume/cancel races and prevent stale updates from resurrecting terminal tasks.
- Enforce budgets for runtime, commands, model calls, and spend before starting work and between DAG waves.
- Keep mandatory verification failure as a hard delivery blocker. Repairs must re-run all applicable gates.
- Exit: live end-to-end runs for representative project types with artifacts and auditable evidence.

### P5 — Generated-project quality and live-usage battery
- Exercise each project generator through the public orchestrator, not only by calling template functions directly.
- Run the generated output: syntax/type checks, tests, build, and smoke behavior as appropriate to its language.
- Stress adversarial inputs (empty, huge, Unicode/control characters, quotes, traversal attempts, malformed dates, concurrent operations, and injection-shaped text).
- Fix each confirmed defect in source and add a regression test plus a numbered finding in `notes/LIVE_USAGE_FINDINGS.md`.
- Exit: no unresolved reproducible critical/high-severity findings in the audited surfaces; evidence recorded.

### P6 — Webhook and external integration reliability
- Test timeouts, DNS/connection failures, receiver 4xx/5xx, retry budget, exponential backoff, jitter, deduplication, and delivery receipts.
- Keep provider fallbacks bounded and observable; never expose tokens in logs or error messages.
- Exit: deterministic failure-mode tests and clear operational status for exhausted retries.

### P7 — API, filesystem, and security boundaries
- Review schema limits, authentication/authorization, rate limits, path traversal and symlink behavior, generated content, upload sizes, and error disclosure.
- Verify all writes resolve under the intended workspace and that failed generation cleans up partial artifacts safely.
- Exit: negative tests for all identified trust boundaries; no accidental broadening of privileges.

### P8 — Release and operational readiness
- Review container build/runtime user, health checks, dependency drift, CI permissions, workflow triggers, and supply-chain risk.
- Publish documented setup, configuration, diagnostics, backups/restore, and rollback guidance.
- Exit: reproducible clean install, green full CI, working health checks, and a release checklist with no unexplained failures.

## Execution order for the current campaign

1. P0: re-check current main CI and repository state. (Baseline currently has a green run.)
2. P1: harden `forge_upgrade/exec_runner.py` and introduce focused tests. This is the first implementation batch.
3. Add this plan to the repo and keep `AGENT_PROGRESS.md` in sync with evidence and the next exact action.
4. Run PR CI. Diagnose and repair every newly exposed issue; do not merge on a partial pass.
5. Continue P2/P3 in subsequent small batches, using the same tests-first, evidence-gated process.

## Definition of done

A plan checkbox is complete only when its source change is committed, focused tests and the full required checks pass on the candidate commit, generated artifacts have been run where applicable, and evidence (commit/PR/run links and any remaining risks) is documented. A green CI run is necessary but not sufficient evidence that every product path is production-ready.

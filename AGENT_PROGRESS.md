# FORGE Engineering Progress

> Roadmap: [FORGE_MASTER_PLAN.md](FORGE_MASTER_PLAN.md). The checklist below preserves the live-usage campaign history; the master plan is the active cross-workstream source of truth.

## Active engineering campaign — 2026-10-22

**Baseline:** `main` at `00ce5fe1e377a81c6e510c90b10c94397ea3e66d`; the latest recorded main workflow passed Ruff, pytest, and Docker build.

**Feature branch:** `feat/forge-master-plan-execution-hardening`

- [x] Add a phased master plan with safety rules, priorities, and exit criteria.
- [x] Replace whole-output subprocess buffering with bounded per-stream capture while continuously draining both pipes.
- [x] Add positive finite timeout validation and explicit output-truncation metadata.
- [x] Add process-group termination and child reaping on timeout/cancellation paths.
- [x] Add regression tests for exit codes, stream capture, output bounds, timeouts, cancellation, and invalid configuration.
- [ ] Wait for the candidate branch's full CI and Docker build; fix every observed failure before merge.
- [ ] Continue P2/P3: DAG state invariants, blocked descendants, idempotency lifecycle/concurrency, and end-to-end generated-project checks.

**Acceptance rule:** do not mark the implementation complete until CI passes on the exact final head SHA and the PR contains the observed results. Cancellation and output truncation tests must pass; no CI bypasses or test skips to conceal regressions.

## Next exact action

Inspect the newest GitHub Actions run for this branch. If CI fails, fetch the failing job log and fix the underlying defect on this branch, add a focused regression test, and re-run all checks. If it passes, review execution call sites for policy enforcement and then begin the P2 DAG-state audit described in the master plan.

---

Task: operate the FORGE agent like a real user across its full capability
surface, push it to adversarial/extreme conditions, fix every real bug found
in code (not just document it), add regression tests, and leave the agent
demonstrably more robust. "Tests pass" is not sufficient evidence — every
fix must be verified by actually running the generated output. Sustained,
multi-hour effort; do not stop early.

Findings 1-21 already fixed, verified live, and documented in
`notes/LIVE_USAGE_FINDINGS.md` (see that file for full root-cause/repro/fix
write-ups). This file tracks the campaign checklist going forward.

## Checklist

- [x] 1. Rebuild dev environment (`.venv` was not persisted across session) — done, full suite 459 passed/1 skipped/0 failed.
- [x] 2. Commit + push Findings 17-21 batch (dead JS handlers, script data-loss bugs x3, broken contact library) — commit `260ddfb`, pushed.
- [x] 3. Library generator adversarial audit: probed all 17 entities x edge-case inputs (empty/None/unicode/malformed). Found + fixed Finding 22 (`days_between` raw ValueError on malformed date). Everything else degrades gracefully. 460 passed/1 skipped.
- [x] 4. Script generator goal-phrasing audit. Found + fixed Finding 23 (critical): "scrapes a website" misrouted to the WEBSITE generator entirely, because `_detect_kind` checked WEBSITE's generic keywords before SCRIPT's. Reordered priority, added regression tests. 465 passed/1 skipped.
- [x] 5. API (FastAPI) generator adversarial audit (14-point live TestClient probe). Found + fixed Finding 24 (unbounded string fields = DoS vector, 2MB payload accepted). All other 13 adversarial cases already handled correctly. 467 passed/1 skipped.
- [x] 6. CLI generator adversarial audit. Found + fixed Finding 25 (CRITICAL): concurrent invocations crashed (shared tmp filename) AND silently lost data (unlocked read-modify-write race) — 20 concurrent `add`s only left 12 records. Fixed with pid-suffixed tmp files + fcntl cross-process locking around the full load-modify-save cycle. Verified live at 20-way and 50-way concurrency plus mixed add/update/delete. Also fixed a pre-existing minor lint bug (unused p_cmd var) found while re-linting. 469 passed/1 skipped.
- [x] 7. Extended dead-element sweep to `<input>`/`<select>` (anchors checked too, none dead). Found + fixed Finding 26: ecommerce checkout form collected cust-name/cust-email/cust-address but never read them. Fixed with a real confirmation reflecting submitted data; verified live via jsdom submit-event dispatch. 470 passed/1 skipped.
- [x] 8. Found + fixed Finding 27 (critical): pause/cancel racing an in-flight DAG wave was silently discarded by step_task()'s stale-state overwrite; a cancelled task could be resurrected to RUNNING and keep executing. Fixed, 3 regression tests added, 473 passed/1 skipped.
- [~] 9. Orchestrator: repeated/idempotent submission of the same goal (double-submit, retry-after-timeout-but-it-actually-succeeded). **Current step.**
- [ ] 10. Webhooks: deliberate stress test of delivery under receiver failure modes (timeout, 5xx, connection refused, DNS failure, slow-loris) beyond the incidental 3-retry observation from Finding 13.
- [ ] 11. Unicode/injection-style goal content: broaden beyond the existing NUL-byte sanitize fix — RTL overrides, zero-width chars, script-injection-looking strings, extremely long single-token goals.
- [ ] 12. Multi-project-kind run through the live orchestrator end-to-end (not direct generator calls) to confirm delivery packaging + verification pipeline either catch generator-level issues automatically or confirm (and document) that they currently don't.
- [ ] 13. Final full-suite verification + lint + commit + push + update `notes/LIVE_USAGE_FINDINGS.md` summary.

## Notes
- Always verify fixes by actually regenerating and running the output (jsdom for JS, real subprocess/pytest for Python), not just reading source.
- Every real bug found: root-cause in generator code (`app/agents/synthesis.py`, `app/templates/web_studio/generator.py`, or relevant module), fix, regenerate, live-verify, add regression test, log as a new numbered Finding in `notes/LIVE_USAGE_FINDINGS.md`.
- Clean `.scratch/` after each audit; never commit it.
- Commit after each checklist item completes with tests green.

# FORGE Live-Usage Hardening Campaign — Progress

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
- [~] 7. Website generator: extend the "dead interactive element" sweep to `<a href>`, `<select>`, `<input type="range">`/other input types across all 4 templates. **Current step.**
- [ ] 8. Orchestrator: pause/resume/cancel mid-execution races against a real long-running task (not just the cancel-route consistency already covered by Finding 13).
- [ ] 9. Orchestrator: repeated/idempotent submission of the same goal (double-submit, retry-after-timeout-but-it-actually-succeeded).
- [ ] 10. Webhooks: deliberate stress test of delivery under receiver failure modes (timeout, 5xx, connection refused, DNS failure, slow-loris) beyond the incidental 3-retry observation from Finding 13.
- [ ] 11. Unicode/injection-style goal content: broaden beyond the existing NUL-byte sanitize fix — RTL overrides, zero-width chars, script-injection-looking strings, extremely long single-token goals.
- [ ] 12. Multi-project-kind run through the live orchestrator end-to-end (not direct generator calls) to confirm delivery packaging + verification pipeline either catch generator-level issues automatically or confirm (and document) that they currently don't.
- [ ] 13. Final full-suite verification + lint + commit + push + update `notes/LIVE_USAGE_FINDINGS.md` summary.

## Notes
- Always verify fixes by actually regenerating and running the output (jsdom for JS, real subprocess/pytest for Python), not just reading source.
- Every real bug found: root-cause in generator code (`app/agents/synthesis.py`, `app/templates/web_studio/generator.py`, or relevant module), fix, regenerate, live-verify, add regression test, log as a new numbered Finding in `notes/LIVE_USAGE_FINDINGS.md`.
- Clean `.scratch/` after each audit; never commit it.
- Commit after each checklist item completes with tests green.

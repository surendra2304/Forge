# FORGE DIARY MAINTENANCE SPECIFICATION

**Document Version**: 1.0.0  
**Scope**: All current and future development, auditing, and maintenance of **Forge**.

---

## 1. Core Principles

1. **Chronological & Never-Ending**: The diary begins on **25 August 2026** (Day 1) and continues indefinitely.
2. **One Detailed File Per Calendar Day**: Every development session must be logged in `diary/YYYY-MM-DD.md`.
3. **Master Index Synchronization**: `FORGE_DIARY.md` is the consolidated index providing top-level summaries and navigation links to all daily files.
4. **Immutable Historical Records**: Past completed days are historical artifacts and must not be silently rewritten.
5. **Additive Corrections**: If earlier claims, assumptions, or implementations are discovered to be inaccurate or superseded, record corrections in today's entry or a dedicated `## Corrections to Earlier Information` section.
6. **Strict Truthfulness**: Every reported test result, commit, API interaction, and bug fix must reflect verifiable reality. Never fabricate status.
7. **Zero Secrets**: Secrets, passwords, API keys, credentials, or private environment variables NEVER belong in `FORGE_DIARY.md`, `diary/*.md`, or any repo file.
8. **Permanent Bug Numbering**: Bugs are tracked with unique, permanent identifiers (e.g. Bug #01). Identifiers are never reused or deleted.

---

## 2. File Organization

```text
Forge/
├── FORGE_DIARY.md                  # Master chronological diary index
├── FORGE_DIARY_SPEC.md             # This permanent maintenance specification
├── diary/                          # Day-by-day detailed raw chronicle logs
│   └── 2026-08-25.md
├── scripts/
│   └── update_forge_diary.py       # Helper script for diary creation & validation
└── .agents/
    └── rules/
        └── forge_diary_policy.md   # Agent policy rule for diary enforcement
```

---

## 3. Standard Daily Entry Schema

Every daily entry in `diary/YYYY-MM-DD.md` must follow the standard structure below (omit irrelevant sections):

```markdown
# FORGE — YYYY-MM-DD

## Daily Summary
## User Directives / Requirements
## Work Performed
## Architecture / Structure Changes
## Files Created
## Files Modified
## Files Deleted
## Tools & Subsystems
## Security Changes
## CLI / UI Changes
## Tests Performed & Test Results
## Bugs / Errors Discovered
### Bug #XX: [Short Title]
- Symptoms:
- Root Cause:
- Fix:
- Commit:
- Verification:
## Important Decisions
## Incidents / Misconfigurations
## Corrections to Earlier Information
## Git Commits
## Current End-of-Day State
## Next Planned Work
```

---

## 4. Master Index (`FORGE_DIARY.md`) Structure

`FORGE_DIARY.md` must maintain:
1. **Project Overview**: Core metadata (Repository, Primary Branch, Inception Date).
2. **Diary Navigation**: Clean chronological link list to each `diary/YYYY-MM-DD.md` file.
3. **Historical Development**: High-level structured summaries of each day's objectives, completed work, bugs fixed, and end-of-day state.

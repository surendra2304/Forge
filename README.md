# Forge 🔨

A centralized development powerhouse and experimental engineering forge.

---

## 📖 Development Diary & Governance

Forge follows a strict, permanent development chronicle architecture inspired by robust engineering governance standards:

- **[Master Diary](FORGE_DIARY.md)**: Consolidated chronological index tracking daily achievements, milestones, and status.
- **[Diary Maintenance Specification](FORGE_DIARY_SPEC.md)**: The structural standard and rules governing all chronicle entries.
- **[Daily Logs](diary/)**: Detailed day-by-day logs recording requirements, architecture changes, files affected, testing outcomes, and bug fixes.
- **[Automation Helper](scripts/update_forge_diary.py)**: Tooling to generate and validate daily diary entries.
- **[Agent Diary Policy](.agents/rules/forge_diary_policy.md)**: Guidelines for AI assistants and contributors.

---

## 🛠️ Repository Layout

```text
Forge/
├── .agents/
│   └── rules/
│       └── forge_diary_policy.md   # Agent memory and diary maintenance policy
├── diary/                          # Day-by-day engineering chronicle
│   └── 2026-08-25.md
├── scripts/
│   └── update_forge_diary.py       # Diary management script
├── .gitignore                      # Git ignore configurations
├── FORGE_DIARY.md                  # Master chronological diary index
├── FORGE_DIARY_SPEC.md             # Diary specification standard
└── README.md                       # Project overview and documentation
```

---

## 🚀 Diary Workflow

To create or synchronize today's diary entry:

```bash
python scripts/update_forge_diary.py
```

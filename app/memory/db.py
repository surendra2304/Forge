"""
SQLite database layer for FORGE using aiosqlite.
Manages connections, schema initialization, and transaction boundaries.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("memory.db")

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    workspace_path TEXT NOT NULL,
    config TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    requirements TEXT NOT NULL DEFAULT '[]',
    mode TEXT NOT NULL DEFAULT 'autonomous',
    workspace_path TEXT NOT NULL,
    max_budget REAL NOT NULL DEFAULT 10.0,
    budget_consumed REAL NOT NULL DEFAULT 0.0,
    state TEXT NOT NULL DEFAULT 'PENDING',
    progress_percentage INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    timestamp TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    file_type TEXT NOT NULL DEFAULT 'text/plain',
    size_bytes INTEGER NOT NULL DEFAULT 0,
    checksum TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS task_graphs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    nodes TEXT NOT NULL DEFAULT '{}',
    edges TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'PENDING',
    current_node_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    task_id TEXT,
    step_number INTEGER NOT NULL DEFAULT 0,
    state_data TEXT NOT NULL DEFAULT '{}',
    checksum TEXT,
    timestamp TEXT NOT NULL,
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_state ON tasks(state);
CREATE INDEX IF NOT EXISTS idx_audit_events_task ON audit_events(task_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_artifacts_task ON artifacts(task_id);
CREATE INDEX IF NOT EXISTS idx_task_graphs_project ON task_graphs(project_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_project ON checkpoints(project_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_step ON checkpoints(project_id, step_number);
"""


class DatabaseManager:
    """Manages SQLite connections and schema migrations."""

    def __init__(self, db_path: Path | None = None):
        self.settings = get_settings()
        self.db_path = db_path or (self.settings.base_dir / self.settings.database_path)

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Async context manager yielding a configured connection."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA journal_mode = WAL;")
            await conn.execute("PRAGMA foreign_keys = ON;")
            yield conn

    async def init_db(self) -> None:
        """Initialize SQLite database tables and indexes."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with self.connection() as conn:
            await conn.executescript(SCHEMA_SQL)
            try:
                await conn.execute("ALTER TABLE tasks ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}';")
            except Exception:
                pass
            await conn.commit()
        logger.info(f"Initialized SQLite database at {self.db_path}")


# Global singleton instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """FastAPI dependency for yielding database connections."""
    async with db_manager.connection() as conn:
        yield conn

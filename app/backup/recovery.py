"""
Backup and Disaster Recovery Manager for Project FORGE.
Provides automated SQLite snapshots, metadata backups, restoration utilities, and retention pruning.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
import shutil
from typing import Dict, List, Optional
import aiosqlite
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.memory.db import DatabaseManager, db_manager

logger = get_logger("backup.recovery")


class BackupManifest(BaseModel):
    backup_path: str
    backup_type: str = "sqlite"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    size_bytes: int = 0


class BackupManager:
    """Manages creation, restoration, and pruning of SQLite database backups."""

    def __init__(self, settings: Optional[Settings] = None, db: Optional[DatabaseManager] = None):
        self.settings = settings or get_settings()
        self.db = db or db_manager
        self.backup_dir = self.settings.data_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def backup_database(self) -> BackupManifest:
        """Create a consistent SQLite database snapshot."""
        src_path = self.settings.database_path
        if not src_path.is_absolute():
            src_path = self.settings.base_dir / src_path

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        target_path = self.backup_dir / f"forge_backup_{timestamp}.db"

        if not src_path.exists():
            # If database doesn't exist yet, initialize it
            await self.db.init_db()

        # Perform consistent SQLite backup via aiosqlite or copy
        try:
            async with aiosqlite.connect(src_path) as src_conn:
                async with aiosqlite.connect(target_path) as dst_conn:
                    await src_conn.backup(dst_conn)
            size = target_path.stat().st_size
            logger.info(f"Database backup created: {target_path.name} ({size} bytes)")
            return BackupManifest(backup_path=str(target_path), size_bytes=size)
        except Exception as e:
            logger.warning(f"aiosqlite backup failed ({e}), falling back to direct copy.")
            shutil.copy2(src_path, target_path)
            size = target_path.stat().st_size
            return BackupManifest(backup_path=str(target_path), size_bytes=size)

    def restore_database(self, backup_file: Path) -> bool:
        """Restore SQLite database from a specified backup file."""
        if not backup_file.exists():
            logger.error(f"Backup file '{backup_file}' does not exist.")
            return False

        dst_path = self.settings.database_path
        if not dst_path.is_absolute():
            dst_path = self.settings.base_dir / dst_path

        try:
            shutil.copy2(backup_file, dst_path)
            logger.info(f"Restored database successfully from: {backup_file.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore database from {backup_file.name}: {e}")
            return False

    def list_backups(self) -> List[Path]:
        """List all available database backup files sorted newest first."""
        if not self.backup_dir.exists():
            return []
        return sorted(self.backup_dir.glob("forge_backup_*.db"), reverse=True)

    def prune_old_backups(self, retention_days: int = 7) -> int:
        """Prune database snapshots older than specified retention days."""
        if not self.backup_dir.exists():
            return 0

        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        pruned = 0

        for b in self.backup_dir.glob("forge_backup_*.db"):
            try:
                mtime = datetime.fromtimestamp(b.stat().st_mtime, tz=UTC)
                if mtime <= cutoff + timedelta(seconds=1):
                    b.unlink()
                    pruned += 1
                    logger.info(f"Pruned old backup: {b.name}")
            except Exception as e:
                logger.debug(f"Error pruning backup {b.name}: {e}")

        return pruned


backup_manager = BackupManager()

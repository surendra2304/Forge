"""
Unit tests for Production Hardening, Health Probes, Metrics, Security, and Backup Recovery.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.backup.recovery import BackupManager
from app.main import app
from app.memory.db import DatabaseManager, db_manager
from app.monitoring.audit import AuditLogger
from app.security.api_keys import APIKeyManager, RateLimiter


@pytest.mark.asyncio
async def test_health_liveness_and_readiness():
    await db_manager.init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Liveness
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

        # Readiness
        res_ready = await client.get("/health/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "ready"
        assert res_ready.json()["database_connected"] is True

        # Detailed Diagnostics
        res_diag = await client.get("/health/detailed")
        assert res_diag.status_code == 200
        data = res_diag.json()
        assert "database" in data
        assert "ai_universe" in data
        assert "system_metrics" in data


@pytest.mark.asyncio
async def test_prometheus_metrics_export():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/metrics")
        assert res.status_code == 200
        assert "forge_uptime_seconds" in res.text
        assert "forge_requests_total" in res.text
        assert "forge_system_cpu_percent" in res.text


def test_rate_limiter_sliding_window():
    limiter = RateLimiter(limit_per_hour=3)
    client_id = "test_client_key"

    assert limiter.is_allowed(client_id) is True
    assert limiter.is_allowed(client_id) is True
    assert limiter.is_allowed(client_id) is True
    # 4th request exceeds limit
    assert limiter.is_allowed(client_id) is False
    assert limiter.get_remaining(client_id) == 0


def test_api_key_manager():
    mgr = APIKeyManager()
    mgr.add_key("key_primary")
    mgr.add_key("valid_test_key_123")
    assert mgr.validate_key("valid_test_key_123") is True
    assert mgr.validate_key("invalid_key") is False
    mgr.revoke_key("valid_test_key_123")
    assert mgr.validate_key("valid_test_key_123") is False
    assert mgr.validate_key("key_primary") is True


def test_audit_logger(tmp_path: Path):
    with patch("app.monitoring.audit.get_settings") as mock_settings:
        mock_settings.return_value.data_dir = tmp_path
        logger = AuditLogger()
        logger.settings = mock_settings.return_value

        event = logger.record_event(
            event_type="task_submitted",
            task_id="task_audit_01",
            raw_key="super_secret_api_key_value",
            details={"goal": "Build dashboard"},
        )
        assert event.event_type == "task_submitted"
        assert "secret" not in (event.client_key_id or "")
        assert "..." in (event.client_key_id or "")


@pytest.mark.asyncio
async def test_backup_and_restore(tmp_path: Path):
    db_path = tmp_path / "data" / "source.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = DatabaseManager(db_path=db_path)
    await db.init_db()

    with patch("app.backup.recovery.get_settings") as mock_settings:
        mock_settings.return_value.data_dir = tmp_path / "data"
        mock_settings.return_value.database_path = db_path
        mock_settings.return_value.base_dir = tmp_path

        mgr = BackupManager(settings=mock_settings.return_value, db=db)
        manifest = await mgr.backup_database()

        assert Path(manifest.backup_path).exists()
        assert manifest.size_bytes > 0

        # Test listing
        backups = mgr.list_backups()
        assert len(backups) == 1

        # Test restore
        restored = mgr.restore_database(Path(manifest.backup_path))
        assert restored is True

"""
Health, Readiness, Diagnostics, and Prometheus Metrics Endpoints for Project FORGE.
"""

import time
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.integrations.ai_universe_deep import deep_ai_universe
from app.memory.db import db_manager
from app.monitoring.production_monitor import AlertStatus, production_monitor

health_router = APIRouter(tags=["Health & Monitoring"])


class LivenessResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    uptime_seconds: float
    database_connected: bool = True


class ReadinessResponse(BaseModel):
    status: str = "ready"
    database_connected: bool = True
    workspaces_writable: bool = True


class DiagnosticResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    environment: str = "development"
    database: Dict[str, Any]
    ai_universe: Dict[str, Any]
    system_metrics: Dict[str, Any]
    alerts: AlertStatus


@health_router.get("/health", response_model=LivenessResponse, summary="Liveness Probe")
async def health_liveness():
    """Lightweight liveness probe checking that HTTP server is responsive."""
    settings = get_settings()
    sys_m = production_monitor.get_system_metrics()
    return LivenessResponse(
        status="ok",
        version=settings.app_version,
        uptime_seconds=sys_m["uptime_seconds"],
        database_connected=True,
    )


@health_router.get("/health/ready", response_model=ReadinessResponse, summary="Readiness Probe")
async def health_readiness():
    """Readiness probe checking database connectivity and workspace filesystem write access."""
    db_ok = False
    ws_ok = False

    try:
        async with db_manager.connection() as conn:
            cursor = await conn.execute("SELECT 1")
            row = await cursor.fetchone()
            db_ok = row is not None and row[0] == 1
    except Exception:
        db_ok = False

    try:
        settings = get_settings()
        ws_dir = settings.base_dir / settings.workspaces_dir if not settings.workspaces_dir.is_absolute() else settings.workspaces_dir
        ws_dir.mkdir(parents=True, exist_ok=True)
        test_file = ws_dir / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        ws_ok = True
    except Exception:
        ws_ok = False

    if not db_ok or not ws_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database_connected": db_ok,
                "workspaces_writable": ws_ok,
            },
        )

    return ReadinessResponse(
        status="ready",
        database_connected=db_ok,
        workspaces_writable=ws_ok,
    )


@health_router.get("/health/detailed", response_model=DiagnosticResponse, summary="Detailed Diagnostics")
async def health_detailed():
    """Comprehensive diagnostic diagnostics across storage, AI-Universe, and system resources."""
    settings = get_settings()

    # DB Health & Latency
    db_start = time.time()
    db_ok = True
    try:
        async with db_manager.connection() as conn:
            cursor = await conn.execute("SELECT COUNT(*) FROM tasks")
            row = await cursor.fetchone()
            task_count = row[0] if row else 0
    except Exception:
        db_ok = False
        task_count = 0
    db_latency_ms = round((time.time() - db_start) * 1000.0, 2)

    # AI-Universe Health
    aiu_ok = deep_ai_universe.check_health()

    sys_m = production_monitor.get_system_metrics()
    alerts = production_monitor.check_alerts()

    overall_status = "healthy"
    if alerts.has_active_alerts:
        overall_status = "degraded"
    if not db_ok:
        overall_status = "unhealthy"

    return DiagnosticResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.env,
        database={
            "connected": db_ok,
            "latency_ms": db_latency_ms,
            "total_tasks_recorded": task_count,
        },
        ai_universe={
            "healthy": aiu_ok,
            "url": settings.ai_universe_url,
        },
        system_metrics=sys_m,
        alerts=alerts,
    )


@health_router.get("/metrics", summary="Prometheus Metrics Exporter")
async def get_metrics():
    """Expose Prometheus-compatible metrics for scraping."""
    metrics_text = production_monitor.export_prometheus_metrics()
    return Response(content=metrics_text, media_type="text/plain; version=0.0.4")

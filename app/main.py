"""
FORGE Application Entry Point.
FastAPI initialization with lifespan lifecycle management, middleware, and routers.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import hmac

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.analytics import analytics_router
from app.api.health import health_router
from app.api.improvement import improvement_router
from app.api.marketplace import marketplace_router, task_template_router
from app.api.routes import router as api_router
from app.api.tasks import tasks_router
from app.api.delegate import delegate_router
from app.api.websocket import ws_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.dashboard.routes import dashboard_router
from app.memory.db import db_manager
from app.optimization.performance import performance_optimizer

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle handler."""
    settings = get_settings()
    setup_logging(debug=settings.debug)
    logger.info(f"Starting {settings.app_name} v{settings.app_version} ({settings.env})")

    # Ensure runtime directories exist
    settings.ensure_directories()

    # Initialize SQLite database schema and optimize PRAGMAs
    await db_manager.init_db()
    await performance_optimizer.optimize_sqlite_pragmas(db_manager)
    logger.info("Database schemas initialized and performance PRAGMAs tuned.")

    yield

    logger.info(f"Shutting down {settings.app_name}...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="FORGE: Autonomous Software Engineering Engine for goal-driven software synthesis and verification.",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def require_production_api_key(request: Request, call_next):
        """Fail closed for public production routes while leaving health probes public."""
        from app.config.production import EnvironmentType, production_settings

        if production_settings.env != EnvironmentType.PRODUCTION:
            return await call_next(request)
        if request.url.path in {
            "/health", "/health/ready", "/docs", "/redoc", "/openapi.json",
        } or request.url.path.startswith("/static/"):
            return await call_next(request)

        configured_key = production_settings.forge_api_key or ""
        if len(configured_key) < 32 or configured_key.lower() in {
            "forge_api", "change-me", "changeme", "password", "secret",
        }:
            return JSONResponse(
                status_code=503,
                content={"error": "service_auth_unconfigured", "detail": "A unique FORGE_API_KEY is required."},
            )

        provided_key = request.headers.get("X-API-Key", "")
        authorization = request.headers.get("Authorization", "")
        if not provided_key and authorization.lower().startswith("bearer "):
            provided_key = authorization[7:].strip()
        if not provided_key:
            return JSONResponse(status_code=401, content={"error": "unauthorized"})
        if not hmac.compare_digest(provided_key.encode(), configured_key.encode()):
            return JSONResponse(status_code=403, content={"error": "forbidden"})
        return await call_next(request)

    # Configure CORS for local development and UI dashboards
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Apply GZip compression for responses > 1KB
    performance_optimizer.apply_fastapi_optimizations(app)

    # Register API routers
    app.include_router(health_router, tags=["Health & Diagnostics"])
    app.include_router(api_router, tags=["Core API"])
    app.include_router(api_router, prefix="/api/v1", tags=["API v1"])
    app.include_router(tasks_router, prefix="/api", tags=["Tasks"])
    app.include_router(tasks_router, prefix="/api/v1", tags=["Tasks v1"])
    app.include_router(delegate_router, prefix="/api/v1", tags=["FRIDAY Universe Forge Delegation"])
    app.include_router(analytics_router, prefix="/api", tags=["Analytics"])
    app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics v1"])
    app.include_router(improvement_router, prefix="/api", tags=["Self-Improvement"])
    app.include_router(improvement_router, prefix="/api/v1", tags=["Self-Improvement v1"])
    app.include_router(marketplace_router, tags=["Marketplace"])
    app.include_router(task_template_router, tags=["Tasks"])
    app.include_router(ws_router, tags=["WebSockets"])
    app.include_router(dashboard_router, tags=["Web Dashboard"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

"""
Pytest fixtures and configuration for FORGE test suite.
"""

import asyncio
from pathlib import Path
import shutil
import tempfile
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import create_app
from app.memory.db import DatabaseManager
from app.memory.state_store import StateStore
from app.providers.direct import DirectProvider


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop per test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Path:
    """Provide an isolated temporary directory for test storage."""
    d = tempfile.mkdtemp(prefix="forge_test_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest_asyncio.fixture
async def test_db_manager(temp_dir: Path) -> DatabaseManager:
    """Initialize a clean temporary SQLite database manager."""
    db_path = temp_dir / "test_forge.db"
    manager = DatabaseManager(db_path=db_path)
    await manager.init_db()
    return manager


@pytest_asyncio.fixture
async def state_store(test_db_manager: DatabaseManager) -> StateStore:
    """Provide a StateStore bound to the temporary test database."""
    return StateStore(test_db_manager)


@pytest.fixture
def direct_provider() -> DirectProvider:
    """Provide a standard DirectProvider."""
    return DirectProvider(model_name="test-direct")


@pytest_asyncio.fixture
async def async_client(test_db_manager: DatabaseManager, temp_dir: Path) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient configured with overridden database and workspace paths."""
    from app.memory import db as db_module
    from app.api import routes as routes_module

    app = create_app()

    # Override db_manager in modules
    original_manager = db_module.db_manager
    db_module.db_manager = test_db_manager
    routes_module.db_manager = test_db_manager

    # Override settings workspace dir
    def get_test_settings() -> Settings:
        settings = Settings()
        settings.workspaces_dir = temp_dir / "workspaces"
        settings.data_dir = temp_dir / "data"
        settings.database_path = temp_dir / "test_forge.db"
        settings.ensure_directories()
        return settings

    app.dependency_overrides[get_settings] = get_test_settings
    app.dependency_overrides[routes_module.get_state_store] = lambda: StateStore(test_db_manager)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    db_module.db_manager = original_manager
    routes_module.db_manager = original_manager

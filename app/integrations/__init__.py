"""
Integrations subsystem for Project FORGE.
"""

from app.integrations.ai_universe_client import (
    AIUniverseClient,
    AIUniverseResponse,
    get_ai_universe_client,
)

__all__ = [
    "AIUniverseClient",
    "AIUniverseResponse",
    "get_ai_universe_client",
]

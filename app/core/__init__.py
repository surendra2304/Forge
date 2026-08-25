"""
Core settings and logging configurations for FORGE.
"""

from app.core.config import Settings, get_settings
from app.core.logging import setup_logging, get_logger

__all__ = ["Settings", "get_settings", "setup_logging", "get_logger"]

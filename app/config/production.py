"""
Production Configuration for Project FORGE.
Defines environment-aware runtime settings, rate limit thresholds, and security hardening rules.
"""

import os
import secrets
from enum import Enum

from pydantic import BaseModel, Field


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ProductionSettings(BaseModel):
    """Production-grade security, logging, and operational configuration."""
    env: EnvironmentType = Field(
        default_factory=lambda: EnvironmentType(os.getenv("FORGE_ENV", "development").lower())
    )
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    metrics_enabled: bool = Field(default=True)
    slow_query_threshold_seconds: float = Field(default=1.0)

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    default_rate_limit: int = Field(default=100)  # requests per hour

    # API Security
    api_key_required: bool = Field(
        default_factory=lambda: os.getenv("API_KEY_REQUIRED", "false").lower() in ["true", "1", "yes"]
    )
    forge_api_key: str | None = Field(
        default_factory=lambda: os.getenv("FORGE_API_KEY")
    )
    secret_key: str = Field(
        default_factory=lambda: os.getenv("FORGE_SECRET_KEY", secrets.token_hex(32))
    )

    # Network
    cors_origins: list[str] = Field(
        default_factory=lambda: [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    )

    # Hardening
    secure_cookies: bool = True
    csrf_protection: bool = True
    sql_injection_protection: bool = True


production_settings = ProductionSettings()

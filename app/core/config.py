"""
FORGE Application Configuration using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Information
    app_name: str = Field(default="Project FORGE", description="Application display name")
    app_version: str = Field(default="0.1.0", description="Application semantic version")
    debug: bool = Field(default=True, description="Enable debug mode")
    env: str = Field(default="development", description="Environment stage")

    # Network & Server
    host: str = Field(default="0.0.0.0", description="Server bind host")
    port: int = Field(default=8000, description="Server port")

    # Filesystem Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    database_path: Path = Field(default_factory=lambda: Path("data/forge.db"))
    workspaces_dir: Path = Field(default_factory=lambda: Path("workspaces"))
    artifacts_dir: Path = Field(default_factory=lambda: Path("artifacts"))

    # Provider Defaults
    default_provider: str = Field(default="direct", description="Default model provider")
    default_model: str = Field(default="direct-default", description="Default model identifier")
    model_temperature: float = Field(default=0.2, description="Default generation temperature")

    # API Keys (Optional)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    def ensure_directories(self) -> None:
        """Create runtime directories if they do not exist."""
        for path in [self.data_dir, self.database_path.parent, self.workspaces_dir, self.artifacts_dir]:
            abs_path = self.base_dir / path if not path.is_absolute() else path
            abs_path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    settings = Settings()
    settings.ensure_directories()
    return settings

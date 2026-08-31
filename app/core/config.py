"""
FORGE Application Configuration using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Information
    app_name: str = Field(default="Project FORGE", description="Application display name")
    app_version: str = Field(default="2.0.0", description="Application semantic version")
    debug: bool = Field(default=True, description="Enable debug mode")
    env: str = Field(default="production", description="Environment stage")

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
    default_provider: str = Field(
        default="direct",
        validation_alias=AliasChoices("DEFAULT_PROVIDER", "FORGE_DEFAULT_PROVIDER", "default_provider"),
        description="Default model provider: openai, anthropic, direct, or mock",
    )
    default_model: str = Field(
        default="direct-default",
        validation_alias=AliasChoices("DEFAULT_MODEL", "FORGE_DEFAULT_MODEL", "default_model"),
        description="Default model identifier",
    )
    model_temperature: float = Field(
        default=0.2,
        validation_alias=AliasChoices("MODEL_TEMPERATURE", "FORGE_MODEL_TEMPERATURE", "model_temperature"),
        description="Default generation temperature",
    )

    # API Keys (Optional)
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"),
        description="OpenAI API Key",
    )
    openai_default_model: str = Field(
        default="gpt-4o",
        validation_alias=AliasChoices("OPENAI_DEFAULT_MODEL", "openai_default_model"),
        description="Default OpenAI model",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "anthropic_api_key"),
        description="Anthropic API Key",
    )
    anthropic_default_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        validation_alias=AliasChoices("ANTHROPIC_DEFAULT_MODEL", "anthropic_default_model"),
        description="Default Anthropic model",
    )
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "gemini_api_key"),
        description="Gemini API Key",
    )
    github_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GITHUB_TOKEN", "github_token"),
        description="GitHub Personal Access Token or App Token for pushing and PR creation",
    )
    github_repo: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GITHUB_REPO", "github_repo"),
        description="Default GitHub repository (e.g. owner/repo)",
    )
    ai_universe_url: str = Field(
        default="https://inference-3i2b.onrender.com",
        validation_alias=AliasChoices("INFERENCE_URL", "AI_UNIVERSE_URL", "ai_universe_url"),
        description="Base URL for external Inference / AI Universe reasoning engine",
    )
    ai_universe_api_key: str | None = Field(
        default="inference_api",
        validation_alias=AliasChoices("INFERENCE_API_KEY", "AI_UNIVERSE_API_KEY", "ai_universe_api_key"),
        description="API Key for Inference REST API authentication",
    )
    intelx_url: str = Field(
        default="https://intelx-3cz1.onrender.com",
        validation_alias=AliasChoices("INTELX_URL", "FORGE_INTELX_URL", "intelx_url"),
        description="Base URL for IntelX technical research intelligence service",
    )
    intelx_api_key: str | None = Field(
        default="intelx_api",
        validation_alias=AliasChoices("INTELX_API_KEY", "FORGE_INTELX_API_KEY", "intelx_api_key"),
        description="API Key for IntelX Technical Research API authentication",
    )
    futuris_url: str = Field(
        default="https://futuris-x4f4.onrender.com",
        validation_alias=AliasChoices("FUTURIS_URL", "FORGE_FUTURIS_URL", "futuris_url"),
        description="Base URL for Futuris predictive capacity & success intelligence service",
    )
    futuris_api_key: str | None = Field(
        default="futuris_api",
        validation_alias=AliasChoices("FUTURIS_API_KEY", "FORGE_FUTURIS_API_KEY", "futuris_api_key"),
        description="API Key for Futuris API authentication",
    )
    cortex_url: str = Field(
        default="https://cortex-qifr.onrender.com",
        validation_alias=AliasChoices("CORTEX_URL", "NEXUS_URL", "cortex_url"),
        description="Base URL for Cortex Web Operations engine",
    )
    cortex_api_key: str | None = Field(
        default="cortex_api",
        validation_alias=AliasChoices("CORTEX_API_KEY", "NEXUS_API_KEY", "cortex_api_key"),
        description="API Key for Cortex API authentication",
    )



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


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    settings = Settings()
    settings.ensure_directories()
    return settings

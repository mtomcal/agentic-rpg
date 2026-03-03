"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql://postgres:postgres@postgres:5432/agentic_rpg"
    anthropic_api_key: str = ""
    log_level: str = "info"
    host: str = "0.0.0.0"
    port: int = 8080
    model_name: str = "claude-sonnet-4-20250514"

    model_config = {"env_prefix": ""}


settings = Settings()

"""Application configuration."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Application
    app_name: str = "Agentic RPG"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # State Storage
    state_storage_type: str = "json"
    state_storage_path: Path = Path("./gamestate")

    # Development Options
    use_mocks: bool = False

    def validate_config(self) -> None:
        """Validate configuration at startup."""
        if self.state_storage_type == "json":
            self.state_storage_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Settings | None = None

def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate_config()
    return _settings

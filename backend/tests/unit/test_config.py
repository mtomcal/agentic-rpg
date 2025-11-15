"""Tests for Configuration."""
from pathlib import Path

from agentic_rpg.config import Settings, get_settings


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = Settings()

        assert settings.app_name == "Agentic RPG"
        assert settings.app_env == "development"
        assert settings.debug is True
        assert settings.log_level == "INFO"

    def test_api_defaults(self):
        """Test API configuration defaults."""
        settings = Settings()

        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000

    def test_cors_defaults(self):
        """Test CORS configuration defaults."""
        settings = Settings()

        assert "http://localhost:3000" in settings.cors_origins

    def test_state_storage_defaults(self):
        """Test state storage configuration defaults."""
        settings = Settings()

        assert settings.state_storage_type == "json"
        assert isinstance(settings.state_storage_path, Path)
        assert str(settings.state_storage_path) == "gamestate"

    def test_development_options_defaults(self):
        """Test development options defaults."""
        settings = Settings()

        assert settings.use_mocks is False

    def test_settings_from_environment(self, monkeypatch):
        """Test loading settings from environment variables."""
        # Set environment variables
        monkeypatch.setenv("APP_NAME", "Test RPG")
        monkeypatch.setenv("APP_ENV", "testing")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("API_PORT", "9000")

        settings = Settings()

        assert settings.app_name == "Test RPG"
        assert settings.app_env == "testing"
        assert settings.debug is False
        assert settings.log_level == "DEBUG"
        assert settings.api_port == 9000

    def test_settings_case_insensitive(self, monkeypatch):
        """Test that environment variables are case-insensitive."""
        monkeypatch.setenv("app_name", "Case Test")

        settings = Settings()

        assert settings.app_name == "Case Test"

    def test_cors_origins_from_environment(self, monkeypatch):
        """Test loading CORS origins from environment."""
        # pydantic-settings expects JSON array format for list types
        monkeypatch.setenv("CORS_ORIGINS", '["http://example.com", "http://test.com"]')

        settings = Settings()

        assert "http://example.com" in settings.cors_origins
        assert "http://test.com" in settings.cors_origins

    def test_state_storage_path_from_environment(self, monkeypatch):
        """Test setting state storage path from environment."""
        monkeypatch.setenv("STATE_STORAGE_PATH", "/tmp/gamestate")

        settings = Settings()

        assert settings.state_storage_path == Path("/tmp/gamestate")

    def test_use_mocks_from_environment(self, monkeypatch):
        """Test setting use_mocks from environment."""
        monkeypatch.setenv("USE_MOCKS", "true")

        settings = Settings()

        assert settings.use_mocks is True

    def test_validate_config_creates_storage_path(self, tmp_path):
        """Test that validate_config creates storage path."""
        storage_path = tmp_path / "test_storage"
        settings = Settings(state_storage_path=storage_path)

        # Path shouldn't exist yet
        assert not storage_path.exists()

        # Validate should create it
        settings.validate_config()

        assert storage_path.exists()
        assert storage_path.is_dir()

    def test_validate_config_with_existing_path(self, tmp_path):
        """Test that validate_config works with existing path."""
        storage_path = tmp_path / "existing_storage"
        storage_path.mkdir()

        settings = Settings(state_storage_path=storage_path)
        settings.validate_config()  # Should not raise

        assert storage_path.exists()

    def test_validate_config_only_for_json_storage(self, tmp_path):
        """Test that validate_config only creates path for json storage."""
        storage_path = tmp_path / "db_storage"
        settings = Settings(
            state_storage_type="database",
            state_storage_path=storage_path
        )

        settings.validate_config()

        # Should not create path for non-json storage
        assert not storage_path.exists()


class TestGetSettings:
    """Test get_settings function."""

    def test_get_settings_returns_settings(self):
        """Test that get_settings returns Settings instance."""
        settings = get_settings()

        assert isinstance(settings, Settings)

    def test_get_settings_returns_singleton(self):
        """Test that get_settings returns same instance."""
        # Note: This test might be fragile if _settings global is not reset
        # In a real scenario, you'd want to reset the global between tests
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_validates_on_first_call(self, tmp_path, monkeypatch):
        """Test that get_settings calls validate_config."""
        # Reset the global settings to test initialization
        import agentic_rpg.config as config_module
        config_module._settings = None

        storage_path = tmp_path / "auto_created"
        monkeypatch.setenv("STATE_STORAGE_PATH", str(storage_path))

        get_settings()

        # validate_config should have been called, creating the path
        assert storage_path.exists()

        # Clean up for other tests
        config_module._settings = None


class TestSettingsModel:
    """Test Settings model configuration."""

    def test_model_config_has_env_file(self):
        """Test that model is configured to read from .env."""
        settings = Settings()

        assert settings.model_config["env_file"] == ".env"
        assert settings.model_config["env_file_encoding"] == "utf-8"
        assert settings.model_config["case_sensitive"] is False

    def test_all_required_fields_have_defaults(self):
        """Test that all fields have defaults (no required fields)."""
        # Should be able to create Settings without any arguments
        settings = Settings()

        assert settings is not None
        assert hasattr(settings, "app_name")
        assert hasattr(settings, "api_host")
        assert hasattr(settings, "state_storage_type")

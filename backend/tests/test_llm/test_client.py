"""Tests for LLM client factory — RED phase."""

from unittest.mock import patch

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from agentic_rpg.llm.client import create_chat_model, LLMConfig


class TestLLMConfig:
    """Test LLMConfig data class."""

    def test_default_values(self):
        config = LLMConfig()
        assert config.provider == "anthropic"
        assert config.model_name == "claude-sonnet-4-20250514"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.max_retries == 3
        assert config.request_timeout == 60.0

    def test_custom_values(self):
        config = LLMConfig(
            provider="openai",
            model_name="gpt-4o",
            temperature=0.2,
            max_tokens=2048,
            max_retries=5,
            request_timeout=30.0,
        )
        assert config.provider == "openai"
        assert config.model_name == "gpt-4o"
        assert config.temperature == 0.2
        assert config.max_tokens == 2048
        assert config.max_retries == 5
        assert config.request_timeout == 30.0

    def test_invalid_provider_rejected(self):
        with pytest.raises(ValueError, match="provider"):
            LLMConfig(provider="invalid_provider")

    def test_temperature_bounds(self):
        config_low = LLMConfig(temperature=0.0)
        assert config_low.temperature == 0.0
        config_high = LLMConfig(temperature=2.0)
        assert config_high.temperature == 2.0
        with pytest.raises(ValueError):
            LLMConfig(temperature=-0.1)
        with pytest.raises(ValueError):
            LLMConfig(temperature=2.1)

    def test_max_tokens_positive(self):
        with pytest.raises(ValueError):
            LLMConfig(max_tokens=0)
        with pytest.raises(ValueError):
            LLMConfig(max_tokens=-1)

    def test_request_timeout_must_be_positive(self):
        with pytest.raises(ValueError):
            LLMConfig(request_timeout=0)
        with pytest.raises(ValueError):
            LLMConfig(request_timeout=-1.0)

    def test_max_retries_allows_zero(self):
        config = LLMConfig(max_retries=0)
        assert config.max_retries == 0


class TestCreateChatModel:
    """Test the create_chat_model factory function."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-123"})
    def test_creates_anthropic_model(self):
        config = LLMConfig(provider="anthropic", model_name="claude-sonnet-4-20250514")
        model = create_chat_model(config)
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-sonnet-4-20250514"
        assert model.temperature == 0.7
        assert model.max_tokens == 4096
        assert model.max_retries == 3

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-456"})
    def test_creates_openai_model(self):
        config = LLMConfig(provider="openai", model_name="gpt-4o")
        model = create_chat_model(config)
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "gpt-4o"
        assert model.temperature == 0.7
        assert model.max_tokens == 4096
        assert model.max_retries == 3

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-123"})
    def test_custom_temperature(self):
        config = LLMConfig(provider="anthropic", temperature=0.2)
        model = create_chat_model(config)
        assert isinstance(model, ChatAnthropic)
        assert model.temperature == 0.2

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-123"})
    def test_custom_max_tokens(self):
        config = LLMConfig(provider="anthropic", max_tokens=2048)
        model = create_chat_model(config)
        assert model.max_tokens == 2048

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-123"})
    def test_default_config_creates_anthropic(self):
        """Default config should produce a ChatAnthropic model."""
        model = create_chat_model()
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-sonnet-4-20250514"

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-123"})
    def test_create_from_settings(self):
        """Factory should be able to create a model from app Settings."""
        from agentic_rpg.config import Settings

        test_settings = Settings(
            anthropic_api_key="test-key-from-settings",
            model_name="claude-sonnet-4-20250514",
        )
        config = LLMConfig.from_settings(test_settings)
        assert config.provider == "anthropic"
        assert config.model_name == "claude-sonnet-4-20250514"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-456"})
    def test_openai_custom_timeout_and_retries(self):
        """Verify timeout and retries are passed to OpenAI model."""
        config = LLMConfig(
            provider="openai",
            model_name="gpt-4o",
            max_retries=0,
            request_timeout=30.0,
        )
        model = create_chat_model(config)
        assert isinstance(model, ChatOpenAI)
        assert model.max_retries == 0
        assert model.request_timeout == 30.0

    def test_unsupported_provider_raises(self):
        """Passing a provider not in the allowed set raises ValueError."""
        with pytest.raises(ValueError, match="provider"):
            LLMConfig(provider="cohere")

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-123"})
    def test_anthropic_request_timeout_propagated(self):
        """request_timeout is passed as 'timeout' to ChatAnthropic constructor."""
        config = LLMConfig(provider="anthropic", request_timeout=45.0)
        model = create_chat_model(config)
        assert isinstance(model, ChatAnthropic)
        # ChatAnthropic stores the timeout as default_request_timeout
        assert model.default_request_timeout == 45.0

"""LLM client factory for creating LangChain chat models."""

from __future__ import annotations

from typing import Literal, Union

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator

from agentic_rpg.config import Settings

SUPPORTED_PROVIDERS = ("anthropic", "openai")


class LLMConfig(BaseModel):
    """Configuration for creating an LLM chat model."""

    provider: Literal["anthropic", "openai"] = "anthropic"
    model_name: str = "claude-sonnet-4-20250514"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)
    max_retries: int = Field(default=3, ge=0)
    request_timeout: float = Field(default=60.0, gt=0)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in SUPPORTED_PROVIDERS:  # pragma: no cover
            raise ValueError(f"Unsupported provider: {v!r}. Must be one of {SUPPORTED_PROVIDERS}")
        return v

    @classmethod
    def from_settings(cls, settings: Settings) -> LLMConfig:
        """Create an LLMConfig from application Settings."""
        return cls(
            provider="anthropic",
            model_name=settings.model_name,
        )


def create_chat_model(
    config: LLMConfig | None = None,
) -> Union[ChatAnthropic, ChatOpenAI]:
    """Create a LangChain chat model from configuration.

    Args:
        config: LLM configuration. Uses defaults if not provided.

    Returns:
        A configured ChatAnthropic or ChatOpenAI instance.
    """
    if config is None:
        config = LLMConfig()

    if config.provider == "anthropic":
        return ChatAnthropic(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            max_retries=config.max_retries,
            timeout=config.request_timeout,
        )
    else:
        return ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            max_retries=config.max_retries,
            request_timeout=config.request_timeout,
        )

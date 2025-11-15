"""Conversation-related data models."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Dict, Any, Optional


class Message(BaseModel):
    """Chat message."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional message metadata"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "role": "user",
                "content": "I want to explore the ancient ruins.",
                "timestamp": "2025-01-01T12:00:00Z",
                "metadata": {"session_id": "session_123"}
            }]
        }
    }


class Conversation(BaseModel):
    """Conversation history."""

    messages: list[Message] = Field(default_factory=list)
    context: list[str] = Field(
        default_factory=list,
        description="Important context from previous messages"
    )
    max_history: int = Field(default=100, description="Maximum messages to keep")

    def add_message(self, message: Message) -> None:
        """Add message and maintain history limit."""
        self.messages.append(message)
        if len(self.messages) > self.max_history:
            self.messages.pop(0)

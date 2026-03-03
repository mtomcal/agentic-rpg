"""Top-level game state Pydantic models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from agentic_rpg.models.character import Character
from agentic_rpg.models.inventory import Inventory
from agentic_rpg.models.story import StoryState
from agentic_rpg.models.world import World


class SessionStatus(StrEnum):
    """Status of a game session."""

    active = "active"
    paused = "paused"
    completed = "completed"
    abandoned = "abandoned"


class Session(BaseModel):
    """Session metadata."""

    session_id: UUID = Field(default_factory=uuid4, description="Unique session identifier")
    player_id: UUID = Field(default_factory=uuid4, description="Player who owns this session")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When the session was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When the state was last modified"
    )
    schema_version: int = Field(default=1, description="State schema version")
    status: SessionStatus = Field(
        default=SessionStatus.active, description="Session status"
    )


class MessageRole(StrEnum):
    """Role of a conversation message sender."""

    player = "player"
    agent = "agent"
    system = "system"


class Message(BaseModel):
    """A message in the conversation history."""

    role: MessageRole = Field(description="Who sent the message")
    content: str = Field(description="Message text")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When the message was sent"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional message metadata"
    )


class Conversation(BaseModel):
    """Conversation history for a game session."""

    history: list[Message] = Field(
        default_factory=list, description="Ordered list of messages"
    )
    window_size: int = Field(default=20, description="Messages to include in agent context")
    summary: str = Field(
        default="", description="Summary of older conversation history"
    )


class GameState(BaseModel):
    """The complete game state for a session."""

    session: Session = Field(default_factory=Session, description="Session metadata")
    character: Character = Field(default_factory=Character, description="Player character")
    inventory: Inventory = Field(default_factory=Inventory, description="Character inventory")
    world: World = Field(default_factory=World, description="World state")
    story: StoryState = Field(default_factory=StoryState, description="Story state")
    conversation: Conversation = Field(
        default_factory=Conversation, description="Conversation history"
    )
    recent_events: list[dict[str, Any]] = Field(
        default_factory=list, description="Recent game events"
    )

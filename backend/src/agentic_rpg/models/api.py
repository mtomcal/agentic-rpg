"""API request and response Pydantic models."""

from uuid import UUID

from pydantic import BaseModel, Field

from agentic_rpg.models.game_state import GameState, Message
from agentic_rpg.models.inventory import Item


class CharacterCreate(BaseModel):
    """Character creation parameters."""

    name: str = Field(description="Character name")
    profession: str = Field(description="Character class or profession")
    background: str = Field(default="", description="Character backstory")


class SessionCreateRequest(BaseModel):
    """Request body for creating a new game session."""

    genre: str = Field(description="Game genre (e.g. fantasy, sci-fi)")
    character: CharacterCreate = Field(description="Character creation data")


class SessionCreateResponse(BaseModel):
    """Response for session creation."""

    session_id: UUID = Field(description="ID of the created session")
    game_state: GameState = Field(description="Initial game state")


class SessionSummary(BaseModel):
    """Summary of a game session for listing."""

    session_id: UUID = Field(description="Session ID")
    character_name: str = Field(description="Character name")
    genre: str = Field(default="", description="Game genre")
    status: str = Field(description="Session status")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class SessionListResponse(BaseModel):
    """Response for listing sessions."""

    sessions: list[SessionSummary] = Field(description="List of session summaries")


class SessionDetailResponse(BaseModel):
    """Response for getting session details."""

    game_state: GameState = Field(description="Full game state")


class DeleteResponse(BaseModel):
    """Response for delete operations."""

    success: bool = Field(description="Whether the operation succeeded")


class HealthResponse(BaseModel):
    """Response for health check."""

    status: str = Field(description="Service status")
    version: str = Field(default="0.1.0", description="API version")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error message")
    detail: str | None = Field(default=None, description="Additional error details")


class PlayerActionRequest(BaseModel):
    """WebSocket message: player action."""

    action: str = Field(description="Player's text input")
    session_id: UUID = Field(description="Session to act in")


class AgentResponseMessage(BaseModel):
    """WebSocket message: agent response."""

    content: str = Field(description="Agent's narrative response text")
    session_id: UUID = Field(description="Session this response is for")
    events: list[dict] = Field(default_factory=list, description="Events from this action")


class StateUpdateMessage(BaseModel):
    """WebSocket message: state update pushed to client."""

    session_id: UUID = Field(description="Session that was updated")
    game_state: GameState = Field(description="Updated game state")


# ---------------------------------------------------------------------------
# Game state sub-endpoint response models
# ---------------------------------------------------------------------------


class CharacterSummary(BaseModel):
    """Lightweight character info for the state summary."""

    name: str = Field(description="Character display name")
    profession: str = Field(description="Character class or profession")
    level: int = Field(description="Character level")
    health: float = Field(description="Current health")
    max_health: float = Field(description="Maximum health")


class LocationSummary(BaseModel):
    """Lightweight location info for the state summary."""

    id: str = Field(description="Location identifier")
    name: str = Field(description="Display name")
    description: str = Field(description="Location description")
    connections: list[str] = Field(description="Connected location IDs")


class BeatSummary(BaseModel):
    """Lightweight story beat info for the state summary."""

    summary: str = Field(description="Beat description")
    location: str = Field(description="Where this beat takes place")
    status: str = Field(description="Beat lifecycle status")


class StateSummaryResponse(BaseModel):
    """Response for GET /sessions/{session_id}/state."""

    character: CharacterSummary = Field(description="Character summary")
    location: LocationSummary = Field(description="Current location summary")
    story_beat: BeatSummary | None = Field(
        default=None, description="Active story beat summary"
    )


class InventoryResponse(BaseModel):
    """Response for GET /sessions/{session_id}/inventory."""

    items: list[Item] = Field(description="Items in inventory")
    equipment: dict[str, UUID | None] = Field(description="Equipment slots")


class HistoryResponse(BaseModel):
    """Response for GET /sessions/{session_id}/history."""

    messages: list[Message] = Field(description="Conversation messages")
    total: int = Field(description="Total number of messages")

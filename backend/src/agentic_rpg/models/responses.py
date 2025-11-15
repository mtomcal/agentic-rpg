"""API response models."""
from pydantic import BaseModel, Field
from typing import Dict, Any
from .game_state import GameState


class CreateGameResponse(BaseModel):
    """Response from game creation."""

    session_id: str = Field(..., description="New session ID")
    state: GameState = Field(..., description="Initial game state")


class GameResponse(BaseModel):
    """Response from game action."""

    response: str = Field(..., description="Narrative response")
    state_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="State changes"
    )
    tool_calls: list[str] = Field(
        default_factory=list,
        description="Tools that were executed"
    )

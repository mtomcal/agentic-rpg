"""World-related data models."""
from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime


class NPC(BaseModel):
    """Non-player character."""

    id: str = Field(..., description="Unique NPC identifier")
    name: str = Field(..., description="NPC name")
    description: str = Field(..., description="NPC description")
    personality: str = Field(default="neutral", description="NPC personality type")
    dialogue_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="NPC dialogue state"
    )


class Location(BaseModel):
    """Game location."""

    id: str = Field(..., description="Unique location identifier")
    name: str = Field(..., min_length=1, description="Location name")
    description: str = Field(..., min_length=10, description="Location description")
    type: str = Field(..., description="Location type: city, wilderness, dungeon, etc.")
    connections: list[str] = Field(
        default_factory=list,
        description="Connected location IDs"
    )
    npcs: list[NPC] = Field(default_factory=list, description="NPCs at this location")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Location-specific properties"
    )


class WorldState(BaseModel):
    """Current world state."""

    current_location: Location
    available_locations: list[Location] = Field(default_factory=list)
    time_of_day: str = Field(default="day", description="Current time of day")
    weather: str = Field(default="clear", description="Current weather")
    discovered_locations: list[str] = Field(
        default_factory=list,
        description="Location IDs discovered by player"
    )

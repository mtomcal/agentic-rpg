"""World and location Pydantic models."""

from typing import Any

from pydantic import BaseModel, Field


class Location(BaseModel):
    """A location in the game world."""

    id: str = Field(description="Unique location identifier")
    name: str = Field(description="Display name of the location")
    description: str = Field(default="", description="Location description text")
    connections: list[str] = Field(
        default_factory=list, description="IDs of connected locations"
    )
    npcs_present: list[str] = Field(
        default_factory=list, description="IDs of NPCs at this location"
    )
    items_present: list[str] = Field(
        default_factory=list, description="IDs of items at this location"
    )
    visited: bool = Field(default=False, description="Whether the player has visited")


class World(BaseModel):
    """The game world state."""

    locations: dict[str, Location] = Field(
        default_factory=dict, description="Map of location ID to location data"
    )
    current_location_id: str = Field(
        default="start", description="Player's current location ID"
    )
    discovered_locations: set[str] = Field(
        default_factory=set, description="Set of discovered location IDs"
    )
    world_flags: dict[str, Any] = Field(
        default_factory=dict, description="Key-value flags for world state changes"
    )

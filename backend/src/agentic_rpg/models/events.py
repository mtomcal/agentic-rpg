"""Event-related Pydantic models."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class GameEvent(BaseModel):
    """An immutable record of something that happened in the game."""

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    event_type: str = Field(description="Dotted event type string (e.g. character.stat_changed)")
    payload: dict = Field(default_factory=dict, description="Event payload data")
    source: str = Field(description="Component that emitted the event")
    session_id: UUID = Field(description="Session this event belongs to")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the event occurred"
    )


class EventPayload(BaseModel):
    """Base class for all event payloads."""

    model_config = ConfigDict(frozen=True)


class StatChangedPayload(EventPayload):
    """Payload for character.stat_changed events."""

    stat_name: str = Field(description="Name of the stat that changed")
    old_value: float = Field(description="Previous value")
    new_value: float = Field(description="New value")
    reason: str = Field(default="", description="Why the stat changed")


class LocationChangedPayload(EventPayload):
    """Payload for world.location_changed events."""

    old_location_id: str = Field(description="Previous location ID")
    new_location_id: str = Field(description="New location ID")
    location_name: str = Field(default="", description="Display name of the new location")


class ItemAcquiredPayload(EventPayload):
    """Payload for inventory.item_acquired events."""

    item_id: str = Field(description="ID of the item acquired")
    item_name: str = Field(description="Name of the item")
    quantity: int = Field(default=1, ge=1, description="Number of items acquired")


class ItemRemovedPayload(EventPayload):
    """Payload for inventory.item_removed events."""

    item_id: str = Field(description="ID of the item removed")
    item_name: str = Field(description="Name of the item")
    quantity: int = Field(default=1, ge=1, description="Number of items removed")


class BeatResolvedPayload(EventPayload):
    """Payload for story.beat_resolved events."""

    beat_index: int = Field(description="Index of the resolved beat")
    beat_summary: str = Field(description="Summary of the beat")
    outcome: str = Field(default="", description="How the beat was resolved")

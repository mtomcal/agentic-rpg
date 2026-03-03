"""Story and narrative Pydantic models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class BeatStatus(StrEnum):
    """Lifecycle status of a story beat."""

    planned = "planned"
    active = "active"
    resolved = "resolved"
    skipped = "skipped"
    adapted = "adapted"


class BeatFlexibility(StrEnum):
    """How much a beat can change."""

    fixed = "fixed"
    flexible = "flexible"
    optional = "optional"


class StoryBeat(BaseModel):
    """A planned narrative moment in the story arc."""

    summary: str = Field(description="What should happen at this point (1-2 sentences)")
    location: str = Field(default="any", description="Where this beat takes place")
    trigger_conditions: list[str] = Field(
        default_factory=list, description="Conditions that activate this beat"
    )
    key_elements: list[str] = Field(
        default_factory=list, description="NPCs, items, or events that should be present"
    )
    player_objectives: list[str] = Field(
        default_factory=list, description="What the player can/should do"
    )
    possible_outcomes: list[str] = Field(
        default_factory=list, description="Ways this beat might resolve"
    )
    flexibility: BeatFlexibility = Field(
        default=BeatFlexibility.flexible, description="How much this beat can change"
    )
    status: BeatStatus = Field(
        default=BeatStatus.planned, description="Current lifecycle status"
    )


class AdaptationRecord(BaseModel):
    """Record of a story outline adaptation."""

    reason: str = Field(description="Why the outline was adapted")
    changes: str = Field(description="What changed in the outline")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the adaptation occurred"
    )


class StoryOutline(BaseModel):
    """The story outline for a game session."""

    premise: str = Field(description="2-3 sentence summary of the overall story")
    setting: str = Field(description="World, tone, genre description")
    beats: list[StoryBeat] = Field(
        default_factory=list, description="Ordered sequence of narrative beats"
    )


class StoryState(BaseModel):
    """Full story state for a game session."""

    outline: StoryOutline | None = Field(default=None, description="The story outline")
    active_beat_index: int = Field(default=0, description="Index of the current active beat")
    summary: str = Field(default="", description="Condensed history of resolved beats")
    adaptations: list[AdaptationRecord] = Field(
        default_factory=list, description="History of outline adaptations"
    )

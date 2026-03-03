"""Character-related Pydantic models."""

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class StatusEffectType(StrEnum):
    """Types of status effects."""

    buff = "buff"
    debuff = "debuff"
    condition = "condition"


class StatusEffect(BaseModel):
    """An active status effect on a character."""

    name: str = Field(description="Name of the status effect")
    effect_type: StatusEffectType = Field(description="Category of the effect")
    description: str = Field(default="", description="What this effect does")
    duration: int | None = Field(default=None, description="Remaining turns, None if permanent")
    magnitude: float = Field(default=1.0, description="Strength of the effect")


class Character(BaseModel):
    """A player character in the game."""

    id: UUID = Field(default_factory=uuid4, description="Unique character identifier")
    name: str = Field(description="Character display name")
    profession: str = Field(description="Character class or profession")
    background: str = Field(default="", description="Character backstory")
    stats: dict[str, float] = Field(
        default_factory=lambda: {
            "health": 100.0,
            "max_health": 100.0,
            "energy": 100.0,
            "max_energy": 100.0,
            "money": 0.0,
        },
        description="Character stats (health, energy, money, etc.)",
    )
    status_effects: list[StatusEffect] = Field(
        default_factory=list, description="Active status effects"
    )
    level: int = Field(default=1, ge=1, description="Character level")
    experience: int = Field(default=0, ge=0, description="Experience points")
    location_id: str = Field(default="start", description="Current location ID")

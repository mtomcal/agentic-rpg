"""Character-related data models."""
from pydantic import BaseModel, Field


class CharacterStats(BaseModel):
    """Character statistics."""

    health: int = Field(..., ge=0, description="Current health points")
    max_health: int = Field(..., ge=1, description="Maximum health points")
    energy: int = Field(..., ge=0, description="Current energy points")
    max_energy: int = Field(..., ge=1, description="Maximum energy points")
    money: int = Field(default=0, ge=0, description="Currency amount")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "health": 100,
                "max_health": 100,
                "energy": 50,
                "max_energy": 50,
                "money": 1000
            }]
        }
    }


class Character(BaseModel):
    """Player character model - source of truth for all layers."""

    id: str = Field(..., description="Unique character identifier")
    name: str = Field(..., min_length=1, max_length=50, description="Character name")
    profession: str = Field(..., description="Character's profession")
    stats: CharacterStats
    location: str = Field(..., description="Current location ID")
    status: list[str] = Field(default_factory=list, description="Active status effects")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": "char_123",
                "name": "Jax",
                "profession": "Space Pirate",
                "stats": {
                    "health": 100,
                    "max_health": 100,
                    "energy": 50,
                    "max_energy": 50,
                    "money": 1000
                },
                "location": "cantina_001",
                "status": ["well_rested"]
            }]
        }
    }

"""Inventory-related Pydantic models."""

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ItemType(StrEnum):
    """Types of items."""

    weapon = "weapon"
    armor = "armor"
    consumable = "consumable"
    key = "key"
    misc = "misc"


class Item(BaseModel):
    """An item in the game."""

    id: UUID = Field(default_factory=uuid4, description="Unique item identifier")
    name: str = Field(description="Display name of the item")
    description: str = Field(default="", description="Flavor text for the item")
    item_type: ItemType = Field(description="Category of the item")
    quantity: int = Field(default=1, ge=1, description="Stack count")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Genre-specific item properties"
    )


class Inventory(BaseModel):
    """A character's inventory."""

    items: list[Item] = Field(default_factory=list, description="Items in inventory")
    equipment: dict[str, UUID | None] = Field(
        default_factory=dict, description="Equipment slots mapped to item IDs"
    )
    capacity: int | None = Field(default=None, description="Max inventory size, None for unlimited")

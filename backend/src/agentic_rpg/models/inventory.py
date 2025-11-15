"""Inventory-related data models."""
from pydantic import BaseModel, Field
from typing import Dict, Any


class InventoryItem(BaseModel):
    """Item in inventory."""

    id: str = Field(..., description="Unique item identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: str = Field(default="", description="Item description")
    quantity: int = Field(default=1, ge=1, description="Quantity of item")
    weight: float = Field(default=1.0, ge=0, description="Weight per item")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Item-specific properties"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": "item_sword_001",
                "name": "Plasma Sword",
                "description": "A glowing blade of pure energy",
                "quantity": 1,
                "weight": 2.5,
                "properties": {
                    "damage": 15,
                    "type": "weapon",
                    "rarity": "rare"
                }
            }]
        }
    }


class Inventory(BaseModel):
    """Character inventory."""

    items: list[InventoryItem] = Field(default_factory=list)
    capacity: int = Field(default=20, ge=1, description="Max number of item stacks")
    max_weight: float = Field(default=100.0, ge=0, description="Maximum carry weight")

    @property
    def current_weight(self) -> float:
        """Calculate current total weight."""
        return sum(item.weight * item.quantity for item in self.items)

    @property
    def is_full(self) -> bool:
        """Check if inventory is at capacity."""
        return len(self.items) >= self.capacity

    def can_add(self, item: InventoryItem) -> tuple[bool, str]:
        """Check if item can be added to inventory."""
        if self.is_full:
            return False, "Inventory is full"

        new_weight = self.current_weight + (item.weight * item.quantity)
        if new_weight > self.max_weight:
            return False, f"Too heavy (would be {new_weight}/{self.max_weight})"

        return True, ""

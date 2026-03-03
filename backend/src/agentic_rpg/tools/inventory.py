"""Inventory tools — inspect and modify character inventory."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.events import GameEvent
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.inventory import Item, ItemType


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------
class AddItemInput(BaseModel):
    """Input for add_item."""

    name: str = Field(description="Item name")
    item_type: str = Field(description="Item type (weapon, armor, consumable, key, misc)")
    description: str = Field(default="", description="Item description")
    quantity: int = Field(default=1, ge=1, description="Stack count")


class RemoveItemInput(BaseModel):
    """Input for remove_item."""

    item_name: str = Field(description="Name of item to remove")
    quantity: int | None = Field(default=None, description="Quantity to remove, None for all")


class EquipItemInput(BaseModel):
    """Input for equip_item."""

    item_name: str = Field(description="Name of item to equip")
    slot: str = Field(description="Equipment slot (e.g. weapon, armor, accessory)")


class UnequipItemInput(BaseModel):
    """Input for unequip_item."""

    slot: str = Field(description="Equipment slot to clear")


class UseItemInput(BaseModel):
    """Input for use_item."""

    item_name: str = Field(description="Name of item to use")
    target: str | None = Field(default=None, description="Optional target for the item")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _emit(event_bus: EventBus, game_state: GameState, event_type: str, payload: dict) -> None:
    """Publish an event synchronously via the event bus."""
    event = GameEvent(
        event_type=event_type,
        payload=payload,
        source="tool:inventory",
        session_id=game_state.session.session_id,
    )
    event_bus.publish_sync(event)


def _find_item(game_state: GameState, item_name: str) -> Item | None:
    """Find an item in inventory by name."""
    for item in game_state.inventory.items:
        if item.name == item_name:
            return item
    return None


# ---------------------------------------------------------------------------
# GetInventoryTool
# ---------------------------------------------------------------------------
class GetInventoryTool(BaseTool):
    """Get the current inventory."""

    name: str = "get_inventory"
    description: str = "List current inventory items and equipment."

    game_state: GameState
    event_bus: EventBus

    def _run(self, **kwargs: Any) -> dict:
        return self.game_state.inventory.model_dump()


# ---------------------------------------------------------------------------
# AddItemTool
# ---------------------------------------------------------------------------
class AddItemTool(BaseTool):
    """Add an item to inventory."""

    name: str = "add_item"
    description: str = "Add a new item to the character's inventory."
    args_schema: type = AddItemInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, name: str, item_type: str, description: str = "", quantity: int = 1) -> dict:
        inv = self.game_state.inventory
        if inv.capacity is not None and len(inv.items) >= inv.capacity:
            return {"success": False, "error": "Inventory is full (at capacity)"}

        new_item = Item(
            name=name,
            item_type=ItemType(item_type),
            description=description,
            quantity=quantity,
        )
        inv.items.append(new_item)

        _emit(self.event_bus, self.game_state, "inventory.item_added", {
            "item_name": name,
            "item_type": item_type,
            "quantity": quantity,
        })

        return {"success": True, "item_name": name, "item_id": str(new_item.id)}


# ---------------------------------------------------------------------------
# RemoveItemTool
# ---------------------------------------------------------------------------
class RemoveItemTool(BaseTool):
    """Remove an item from inventory."""

    name: str = "remove_item"
    description: str = "Remove an item from inventory by name."
    args_schema: type = RemoveItemInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, item_name: str, quantity: int | None = None) -> dict:
        item = _find_item(self.game_state, item_name)
        if item is None:
            return {"success": False, "error": f"Item '{item_name}' not found"}

        remove_qty = quantity if quantity is not None else item.quantity
        if remove_qty >= item.quantity:
            self.game_state.inventory.items = [
                i for i in self.game_state.inventory.items if i.name != item_name
            ]
        else:
            item.quantity -= remove_qty

        _emit(self.event_bus, self.game_state, "inventory.item_removed", {
            "item_name": item_name,
            "quantity": remove_qty,
        })

        return {"success": True, "item_name": item_name, "removed": remove_qty}


# ---------------------------------------------------------------------------
# EquipItemTool
# ---------------------------------------------------------------------------
class EquipItemTool(BaseTool):
    """Equip an item to a slot."""

    name: str = "equip_item"
    description: str = "Equip an item from inventory to an equipment slot."
    args_schema: type = EquipItemInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, item_name: str, slot: str) -> dict:
        item = _find_item(self.game_state, item_name)
        if item is None:
            return {"success": False, "error": f"Item '{item_name}' not found"}

        self.game_state.inventory.equipment[slot] = item.id

        _emit(self.event_bus, self.game_state, "inventory.item_equipped", {
            "item_name": item_name,
            "slot": slot,
        })

        return {"success": True, "item_name": item_name, "slot": slot}


# ---------------------------------------------------------------------------
# UnequipItemTool
# ---------------------------------------------------------------------------
class UnequipItemTool(BaseTool):
    """Unequip from a slot."""

    name: str = "unequip_item"
    description: str = "Remove equipment from a slot."
    args_schema: type = UnequipItemInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, slot: str) -> dict:
        equipment = self.game_state.inventory.equipment
        if slot not in equipment or equipment[slot] is None:
            return {"success": False, "error": f"Slot '{slot}' is empty"}

        equipment[slot] = None

        _emit(self.event_bus, self.game_state, "inventory.item_unequipped", {
            "slot": slot,
        })

        return {"success": True, "slot": slot}


# ---------------------------------------------------------------------------
# UseItemTool
# ---------------------------------------------------------------------------
class UseItemTool(BaseTool):
    """Use a consumable item."""

    name: str = "use_item"
    description: str = "Use a consumable item from inventory."
    args_schema: type = UseItemInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, item_name: str, target: str | None = None) -> dict:
        item = _find_item(self.game_state, item_name)
        if item is None:
            return {"success": False, "error": f"Item '{item_name}' not found"}

        if item.item_type != ItemType.consumable:
            return {"success": False, "error": f"Item '{item_name}' is not consumable"}

        if item.quantity <= 1:
            self.game_state.inventory.items = [
                i for i in self.game_state.inventory.items if i.name != item_name
            ]
        else:
            item.quantity -= 1

        _emit(self.event_bus, self.game_state, "inventory.item_used", {
            "item_name": item_name,
            "target": target,
        })

        return {"success": True, "item_name": item_name, "target": target}

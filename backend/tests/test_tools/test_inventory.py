"""Tests for inventory tools — get_inventory, add_item, remove_item,
equip_item, unequip_item, use_item."""

import asyncio

import pytest

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.inventory import ItemType
from agentic_rpg.tools.inventory import (
    AddItemTool,
    EquipItemTool,
    GetInventoryTool,
    RemoveItemTool,
    UnequipItemTool,
    UseItemTool,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _make(cls, gs: GameState, bus: EventBus):
    return cls(game_state=gs, event_bus=bus)


# ===========================================================================
# GetInventoryTool
# ===========================================================================
class TestGetInventoryTool:
    def test_returns_inventory_dict(self, tool_game_state, tool_event_bus):
        tool = _make(GetInventoryTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert len(result["items"]) == 3
        assert result["capacity"] == 20

    def test_item_names(self, tool_game_state, tool_event_bus):
        tool = _make(GetInventoryTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        names = {item["name"] for item in result["items"]}
        assert names == {"Iron Sword", "Health Potion", "Rusty Key"}


# ===========================================================================
# AddItemTool
# ===========================================================================
class TestAddItemTool:
    def test_add_new_item(self, tool_game_state, tool_event_bus):
        tool = _make(AddItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({
            "name": "Shield",
            "item_type": "armor",
            "description": "A wooden shield",
            "quantity": 1,
        })
        assert result["success"] is True
        assert result["item_name"] == "Shield"
        names = [i.name for i in tool_game_state.inventory.items]
        assert "Shield" in names

    def test_add_item_at_capacity(self, tool_game_state, tool_event_bus):
        tool_game_state.inventory.capacity = 3  # already at 3 items
        tool = _make(AddItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({
            "name": "Gem",
            "item_type": "misc",
        })
        assert result["success"] is False
        assert "full" in result["error"].lower() or "capacity" in result["error"].lower()

    def test_add_item_unlimited_capacity(self, tool_game_state, tool_event_bus):
        tool_game_state.inventory.capacity = None
        tool = _make(AddItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({
            "name": "Gem",
            "item_type": "misc",
        })
        assert result["success"] is True

    async def test_emits_item_added_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(AddItemTool, tool_game_state, tool_event_bus)
        tool.invoke({
            "name": "Shield",
            "item_type": "armor",
        })
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "inventory.item_added"
        assert evt.payload["item_name"] == "Shield"


# ===========================================================================
# RemoveItemTool
# ===========================================================================
class TestRemoveItemTool:
    def test_remove_existing_item_by_name(self, tool_game_state, tool_event_bus):
        tool = _make(RemoveItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"item_name": "Rusty Key"})
        assert result["success"] is True
        names = [i.name for i in tool_game_state.inventory.items]
        assert "Rusty Key" not in names

    def test_remove_reduces_quantity(self, tool_game_state, tool_event_bus):
        tool = _make(RemoveItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"item_name": "Health Potion", "quantity": 1})
        assert result["success"] is True
        potion = next(i for i in tool_game_state.inventory.items if i.name == "Health Potion")
        assert potion.quantity == 2

    def test_remove_all_quantity_removes_item(self, tool_game_state, tool_event_bus):
        tool = _make(RemoveItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"item_name": "Health Potion", "quantity": 3})
        assert result["success"] is True
        names = [i.name for i in tool_game_state.inventory.items]
        assert "Health Potion" not in names

    def test_remove_nonexistent_item(self, tool_game_state, tool_event_bus):
        tool = _make(RemoveItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"item_name": "Nonexistent"})
        assert result["success"] is False
        assert "error" in result

    async def test_emits_item_removed_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(RemoveItemTool, tool_game_state, tool_event_bus)
        tool.invoke({"item_name": "Rusty Key"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "inventory.item_removed"
        assert evt.payload["item_name"] == "Rusty Key"


# ===========================================================================
# EquipItemTool
# ===========================================================================
class TestEquipItemTool:
    def test_equip_item(self, tool_game_state, tool_event_bus):
        sword = tool_game_state.inventory.items[0]  # Iron Sword
        tool = _make(EquipItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"item_name": "Iron Sword", "slot": "weapon"})
        assert result["success"] is True
        assert result["slot"] == "weapon"
        assert tool_game_state.inventory.equipment["weapon"] == sword.id

    def test_equip_nonexistent_item(self, tool_game_state, tool_event_bus):
        tool = _make(EquipItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"item_name": "Ghost Blade", "slot": "weapon"})
        assert result["success"] is False
        assert "error" in result

    async def test_emits_item_equipped_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(EquipItemTool, tool_game_state, tool_event_bus)
        tool.invoke({"item_name": "Iron Sword", "slot": "weapon"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "inventory.item_equipped"
        assert evt.payload["item_name"] == "Iron Sword"
        assert evt.payload["slot"] == "weapon"


# ===========================================================================
# UnequipItemTool
# ===========================================================================
class TestUnequipItemTool:
    def test_unequip_item(self, tool_game_state, tool_event_bus):
        sword = tool_game_state.inventory.items[0]
        tool_game_state.inventory.equipment["weapon"] = sword.id
        tool = _make(UnequipItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"slot": "weapon"})
        assert result["success"] is True
        assert tool_game_state.inventory.equipment.get("weapon") is None

    def test_unequip_empty_slot(self, tool_game_state, tool_event_bus):
        tool = _make(UnequipItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"slot": "weapon"})
        assert result["success"] is False
        assert "error" in result

    async def test_emits_item_unequipped_event(self, tool_game_state, tool_event_bus, emitted_events):
        sword = tool_game_state.inventory.items[0]
        tool_game_state.inventory.equipment["weapon"] = sword.id
        tool = _make(UnequipItemTool, tool_game_state, tool_event_bus)
        tool.invoke({"slot": "weapon"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "inventory.item_unequipped"
        assert evt.payload["slot"] == "weapon"


# ===========================================================================
# UseItemTool
# ===========================================================================
class TestUseItemTool:
    def test_use_consumable_reduces_quantity(self, tool_game_state, tool_event_bus):
        tool = _make(UseItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"item_name": "Health Potion"})
        assert result["success"] is True
        potion = next(i for i in tool_game_state.inventory.items if i.name == "Health Potion")
        assert potion.quantity == 2

    def test_use_last_consumable_removes_item(self, tool_game_state, tool_event_bus):
        # Set quantity to 1
        potion = next(i for i in tool_game_state.inventory.items if i.name == "Health Potion")
        potion.quantity = 1
        tool = _make(UseItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"item_name": "Health Potion"})
        assert result["success"] is True
        names = [i.name for i in tool_game_state.inventory.items]
        assert "Health Potion" not in names

    def test_use_non_consumable_fails(self, tool_game_state, tool_event_bus):
        tool = _make(UseItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"item_name": "Iron Sword"})
        assert result["success"] is False
        assert "error" in result

    def test_use_nonexistent_item(self, tool_game_state, tool_event_bus):
        tool = _make(UseItemTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"item_name": "Nonexistent"})
        assert result["success"] is False
        assert "error" in result

    async def test_emits_item_used_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(UseItemTool, tool_game_state, tool_event_bus)
        tool.invoke({"item_name": "Health Potion"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "inventory.item_used"
        assert evt.payload["item_name"] == "Health Potion"

"""Tests for character tools — get_character, update_health, update_energy,
add_status_effect, remove_status_effect, update_money."""

import asyncio

import pytest

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.game_state import GameState
from agentic_rpg.tools.character import (
    AddStatusEffectTool,
    GetCharacterTool,
    RemoveStatusEffectTool,
    UpdateEnergyTool,
    UpdateHealthTool,
    UpdateMoneyTool,
)


# ---------------------------------------------------------------------------
# Helper to build tool with injected deps
# ---------------------------------------------------------------------------
def _make_tool(cls, game_state: GameState, event_bus: EventBus):
    return cls(game_state=game_state, event_bus=event_bus)


# ===========================================================================
# GetCharacterTool
# ===========================================================================
class TestGetCharacterTool:
    def test_returns_character_dict(self, tool_game_state, tool_event_bus):
        tool = _make_tool(GetCharacterTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["name"] == "Aldric"
        assert result["profession"] == "Warrior"
        assert result["stats"]["health"] == 80.0
        assert result["level"] == 2

    def test_includes_status_effects(self, tool_game_state, tool_event_bus):
        tool = _make_tool(GetCharacterTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert len(result["status_effects"]) == 1
        assert result["status_effects"][0]["name"] == "Blessed"

    def test_includes_location(self, tool_game_state, tool_event_bus):
        tool = _make_tool(GetCharacterTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["location_id"] == "tavern"


# ===========================================================================
# UpdateHealthTool
# ===========================================================================
class TestUpdateHealthTool:
    def test_increase_health(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateHealthTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": 10, "reason": "potion"})
        assert result["success"] is True
        assert result["new_value"] == 90.0
        assert tool_game_state.character.stats["health"] == 90.0

    def test_decrease_health(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateHealthTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": -30, "reason": "goblin attack"})
        assert result["success"] is True
        assert result["new_value"] == 50.0

    def test_health_clamped_at_zero(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateHealthTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": -200, "reason": "fatal blow"})
        assert result["new_value"] == 0.0
        assert tool_game_state.character.stats["health"] == 0.0

    def test_health_clamped_at_max(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateHealthTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": 500, "reason": "mega heal"})
        assert result["new_value"] == 100.0
        assert tool_game_state.character.stats["health"] == 100.0

    async def test_emits_stat_changed_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make_tool(UpdateHealthTool, tool_game_state, tool_event_bus)
        tool.invoke({"amount": -10, "reason": "trap"})
        await asyncio.sleep(0)  # let create_task run
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "character.stat_changed"
        assert evt.payload["stat_name"] == "health"
        assert evt.payload["old_value"] == 80.0
        assert evt.payload["new_value"] == 70.0
        assert evt.payload["reason"] == "trap"


# ===========================================================================
# UpdateEnergyTool
# ===========================================================================
class TestUpdateEnergyTool:
    def test_increase_energy(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateEnergyTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": 20, "reason": "rest"})
        assert result["success"] is True
        assert result["new_value"] == 80.0

    def test_decrease_energy(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateEnergyTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": -30, "reason": "sprint"})
        assert result["new_value"] == 30.0

    def test_energy_clamped_at_zero(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateEnergyTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": -200, "reason": "exhaustion"})
        assert result["new_value"] == 0.0

    def test_energy_clamped_at_max(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateEnergyTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": 500, "reason": "full rest"})
        assert result["new_value"] == 100.0

    async def test_emits_stat_changed_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make_tool(UpdateEnergyTool, tool_game_state, tool_event_bus)
        tool.invoke({"amount": -10, "reason": "sprint"})
        await asyncio.sleep(0)  # let create_task run
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "character.stat_changed"
        assert evt.payload["stat_name"] == "energy"
        assert evt.payload["old_value"] == 60.0
        assert evt.payload["new_value"] == 50.0


# ===========================================================================
# UpdateMoneyTool
# ===========================================================================
class TestUpdateMoneyTool:
    def test_add_money(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateMoneyTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": 25, "reason": "loot"})
        assert result["success"] is True
        assert result["new_value"] == 75.0

    def test_remove_money(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateMoneyTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": -20, "reason": "purchase"})
        assert result["new_value"] == 30.0

    def test_money_clamped_at_zero(self, tool_game_state, tool_event_bus):
        tool = _make_tool(UpdateMoneyTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"amount": -200, "reason": "robbery"})
        assert result["new_value"] == 0.0

    async def test_emits_money_changed_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make_tool(UpdateMoneyTool, tool_game_state, tool_event_bus)
        tool.invoke({"amount": 10, "reason": "reward"})
        await asyncio.sleep(0)  # let create_task run
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "character.money_changed"
        assert evt.payload["old_value"] == 50.0
        assert evt.payload["new_value"] == 60.0
        assert evt.payload["reason"] == "reward"


# ===========================================================================
# AddStatusEffectTool
# ===========================================================================
class TestAddStatusEffectTool:
    def test_add_status_effect(self, tool_game_state, tool_event_bus):
        tool = _make_tool(AddStatusEffectTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"effect": "Poisoned", "duration": 5})
        assert result["success"] is True
        assert result["effect"] == "Poisoned"
        effects = [e.name for e in tool_game_state.character.status_effects]
        assert "Poisoned" in effects

    def test_add_permanent_effect(self, tool_game_state, tool_event_bus):
        tool = _make_tool(AddStatusEffectTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"effect": "Cursed"})
        assert result["success"] is True
        added = [e for e in tool_game_state.character.status_effects if e.name == "Cursed"]
        assert len(added) == 1
        assert added[0].duration is None

    async def test_emits_status_effect_added_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make_tool(AddStatusEffectTool, tool_game_state, tool_event_bus)
        tool.invoke({"effect": "Poisoned", "duration": 3})
        await asyncio.sleep(0)  # let create_task run
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "character.status_effect_added"
        assert evt.payload["effect"] == "Poisoned"
        assert evt.payload["duration"] == 3


# ===========================================================================
# RemoveStatusEffectTool
# ===========================================================================
class TestRemoveStatusEffectTool:
    def test_remove_existing_effect(self, tool_game_state, tool_event_bus):
        tool = _make_tool(RemoveStatusEffectTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"effect": "Blessed"})
        assert result["success"] is True
        effects = [e.name for e in tool_game_state.character.status_effects]
        assert "Blessed" not in effects

    def test_remove_nonexistent_effect(self, tool_game_state, tool_event_bus):
        tool = _make_tool(RemoveStatusEffectTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"effect": "Nonexistent"})
        assert result["success"] is False
        assert "error" in result

    async def test_emits_status_effect_removed_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make_tool(RemoveStatusEffectTool, tool_game_state, tool_event_bus)
        tool.invoke({"effect": "Blessed"})
        await asyncio.sleep(0)  # let create_task run
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "character.status_effect_removed"
        assert evt.payload["effect"] == "Blessed"

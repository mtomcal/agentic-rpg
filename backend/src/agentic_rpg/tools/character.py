"""Character tools — inspect and modify character state."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.character import StatusEffect, StatusEffectType
from agentic_rpg.models.events import GameEvent
from agentic_rpg.models.game_state import GameState


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------
class UpdateStatInput(BaseModel):
    """Input for update_health / update_energy."""

    amount: int = Field(description="Amount to add (positive) or subtract (negative)")
    reason: str = Field(description="Why the stat is changing")


class UpdateMoneyInput(BaseModel):
    """Input for update_money."""

    amount: int = Field(description="Amount to add (positive) or subtract (negative)")
    reason: str = Field(description="Why money is changing")


class AddStatusEffectInput(BaseModel):
    """Input for add_status_effect."""

    effect: str = Field(description="Name of the status effect")
    duration: int | None = Field(default=None, description="Duration in turns, None for permanent")


class RemoveStatusEffectInput(BaseModel):
    """Input for remove_status_effect."""

    effect: str = Field(description="Name of the status effect to remove")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _emit(event_bus: EventBus, game_state: GameState, event_type: str, payload: dict) -> None:
    """Publish an event synchronously via the event bus.

    LangChain BaseTool._run is synchronous, so we use the bus's publish_sync
    method which drives subscriber coroutines inline.
    """
    event = GameEvent(
        event_type=event_type,
        payload=payload,
        source="tool:character",
        session_id=game_state.session.session_id,
    )
    event_bus.publish_sync(event)


# ---------------------------------------------------------------------------
# GetCharacterTool
# ---------------------------------------------------------------------------
class GetCharacterTool(BaseTool):
    """Get the current character state."""

    name: str = "get_character"
    description: str = "Get current character state including stats, effects, and location."

    game_state: GameState
    event_bus: EventBus

    def _run(self, **kwargs: Any) -> dict:
        return self.game_state.character.model_dump()


# ---------------------------------------------------------------------------
# UpdateHealthTool
# ---------------------------------------------------------------------------
class UpdateHealthTool(BaseTool):
    """Modify character health, clamped to [0, max_health]."""

    name: str = "update_health"
    description: str = "Modify character health by a given amount. Positive heals, negative damages."
    args_schema: type = UpdateStatInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, amount: int, reason: str) -> dict:
        stats = self.game_state.character.stats
        old_value = stats["health"]
        max_health = stats.get("max_health", 100.0)
        new_value = max(0.0, min(max_health, old_value + amount))
        stats["health"] = new_value

        _emit(self.event_bus, self.game_state, "character.stat_changed", {
            "stat_name": "health",
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
        })

        return {"success": True, "old_value": old_value, "new_value": new_value, "reason": reason}


# ---------------------------------------------------------------------------
# UpdateEnergyTool
# ---------------------------------------------------------------------------
class UpdateEnergyTool(BaseTool):
    """Modify character energy, clamped to [0, max_energy]."""

    name: str = "update_energy"
    description: str = "Modify character energy by a given amount. Positive restores, negative drains."
    args_schema: type = UpdateStatInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, amount: int, reason: str) -> dict:
        stats = self.game_state.character.stats
        old_value = stats["energy"]
        max_energy = stats.get("max_energy", 100.0)
        new_value = max(0.0, min(max_energy, old_value + amount))
        stats["energy"] = new_value

        _emit(self.event_bus, self.game_state, "character.stat_changed", {
            "stat_name": "energy",
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
        })

        return {"success": True, "old_value": old_value, "new_value": new_value, "reason": reason}


# ---------------------------------------------------------------------------
# UpdateMoneyTool
# ---------------------------------------------------------------------------
class UpdateMoneyTool(BaseTool):
    """Add or remove money, clamped at zero."""

    name: str = "update_money"
    description: str = "Add or remove money from the character. Positive adds, negative removes."
    args_schema: type = UpdateMoneyInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, amount: int, reason: str) -> dict:
        stats = self.game_state.character.stats
        old_value = stats["money"]
        new_value = max(0.0, old_value + amount)
        stats["money"] = new_value

        _emit(self.event_bus, self.game_state, "character.money_changed", {
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
        })

        return {"success": True, "old_value": old_value, "new_value": new_value, "reason": reason}


# ---------------------------------------------------------------------------
# AddStatusEffectTool
# ---------------------------------------------------------------------------
class AddStatusEffectTool(BaseTool):
    """Apply a status effect to the character."""

    name: str = "add_status_effect"
    description: str = "Apply a status effect to the character."
    args_schema: type = AddStatusEffectInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, effect: str, duration: int | None = None) -> dict:
        new_effect = StatusEffect(
            name=effect,
            effect_type=StatusEffectType.condition,
            description=effect,
            duration=duration,
        )
        self.game_state.character.status_effects.append(new_effect)

        _emit(self.event_bus, self.game_state, "character.status_effect_added", {
            "effect": effect,
            "duration": duration,
        })

        return {"success": True, "effect": effect, "duration": duration}


# ---------------------------------------------------------------------------
# RemoveStatusEffectTool
# ---------------------------------------------------------------------------
class RemoveStatusEffectTool(BaseTool):
    """Remove a status effect from the character."""

    name: str = "remove_status_effect"
    description: str = "Remove a status effect from the character by name."
    args_schema: type = RemoveStatusEffectInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, effect: str) -> dict:
        effects = self.game_state.character.status_effects
        original_len = len(effects)
        self.game_state.character.status_effects = [
            e for e in effects if e.name != effect
        ]
        if len(self.game_state.character.status_effects) == original_len:
            return {"success": False, "error": f"Status effect '{effect}' not found"}

        _emit(self.event_bus, self.game_state, "character.status_effect_removed", {
            "effect": effect,
        })

        return {"success": True, "effect": effect}

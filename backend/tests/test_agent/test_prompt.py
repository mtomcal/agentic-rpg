"""Tests for agent/prompt.py — system prompt builder."""

import pytest

from agentic_rpg.models.game_state import GameState
from agentic_rpg.agent.prompt import build_system_prompt


class TestBuildSystemPrompt:
    """Tests for the build_system_prompt function."""

    def test_returns_string(self, sample_game_state: GameState):
        """build_system_prompt returns a non-empty string."""
        result = build_system_prompt(sample_game_state)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_includes_character_name(self, sample_game_state: GameState):
        """System prompt includes the character's name."""
        result = build_system_prompt(sample_game_state)
        assert "Aldric" in result

    def test_includes_character_stats(self, sample_game_state: GameState):
        """System prompt includes character stats."""
        result = build_system_prompt(sample_game_state)
        assert "health" in result.lower()
        assert "80" in result  # current health value

    def test_includes_character_profession(self, sample_game_state: GameState):
        """System prompt includes character profession."""
        result = build_system_prompt(sample_game_state)
        assert "Warrior" in result

    def test_includes_location_info(self, sample_game_state: GameState):
        """System prompt includes current location name and description."""
        result = build_system_prompt(sample_game_state)
        assert "The Rusty Flagon" in result
        assert "tavern" in result.lower()

    def test_includes_location_connections(self, sample_game_state: GameState):
        """System prompt includes available connections from current location."""
        result = build_system_prompt(sample_game_state)
        assert "market" in result.lower()
        assert "alley" in result.lower()

    def test_includes_inventory_items(self, sample_game_state: GameState):
        """System prompt includes inventory item names."""
        result = build_system_prompt(sample_game_state)
        assert "Iron Sword" in result
        assert "Health Potion" in result

    def test_includes_story_premise(self, sample_game_state: GameState):
        """System prompt includes the story premise."""
        result = build_system_prompt(sample_game_state)
        assert "lost crown" in result.lower() or "Northern Kingdom" in result

    def test_includes_active_beat(self, sample_game_state: GameState):
        """System prompt includes the active story beat."""
        result = build_system_prompt(sample_game_state)
        assert "market" in result.lower()
        assert "clues" in result.lower() or "map" in result.lower()

    def test_includes_status_effects(self, sample_game_state: GameState):
        """System prompt includes active status effects."""
        result = build_system_prompt(sample_game_state)
        assert "Blessed" in result

    def test_includes_game_master_role(self, sample_game_state: GameState):
        """System prompt establishes the Game Master role."""
        result = build_system_prompt(sample_game_state)
        assert "Game Master" in result

    def test_includes_behavioral_rules(self, sample_game_state: GameState):
        """System prompt includes behavioral guidance."""
        result = build_system_prompt(sample_game_state)
        # Should include at least one rule about player agency
        assert "player" in result.lower()

    def test_includes_setting(self, sample_game_state: GameState):
        """System prompt includes the story setting."""
        result = build_system_prompt(sample_game_state)
        assert "fantasy" in result.lower() or "gritty" in result.lower()

    def test_handles_no_story_outline(self):
        """System prompt handles a game state with no story outline."""
        from agentic_rpg.models.character import Character

        gs = GameState(character=Character(name="Test", profession="Rogue"))
        result = build_system_prompt(gs)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handles_empty_inventory(self):
        """System prompt handles empty inventory gracefully."""
        from agentic_rpg.models.character import Character

        gs = GameState(character=Character(name="Test", profession="Rogue"))
        result = build_system_prompt(gs)
        assert isinstance(result, str)

    def test_includes_npcs_at_location(self, sample_game_state: GameState):
        """System prompt mentions NPCs present at the current location."""
        result = build_system_prompt(sample_game_state)
        assert "bartender" in result.lower()

    def test_includes_recent_events_when_provided(self, sample_game_state: GameState):
        """System prompt includes recent events if present."""
        sample_game_state.recent_events = [
            {"event_type": "character.stat_changed", "payload": {"stat_name": "health", "old_value": 100, "new_value": 80, "reason": "goblin attack"}}
        ]
        result = build_system_prompt(sample_game_state)
        assert "goblin" in result.lower() or "health" in result.lower()

    def test_includes_conversation_summary(self, sample_game_state: GameState):
        """System prompt includes conversation summary if present."""
        sample_game_state.conversation.summary = "The hero arrived and spoke with the bartender."
        result = build_system_prompt(sample_game_state)
        assert "bartender" in result.lower()

    def test_empty_beats_list(self, sample_game_state: GameState):
        """System prompt handles story outline with empty beats list."""
        sample_game_state.story.outline.beats = []
        result = build_system_prompt(sample_game_state)
        # Premise should still be included
        assert "lost crown" in result.lower() or "Northern Kingdom" in result
        # Active beat section should NOT appear
        assert "Active Story Beat" not in result

    def test_out_of_bounds_beat_index(self, sample_game_state: GameState):
        """System prompt handles active_beat_index beyond beats list length."""
        sample_game_state.story.active_beat_index = 999
        result = build_system_prompt(sample_game_state)
        # Should not crash, should still include premise
        assert "lost crown" in result.lower() or "Northern Kingdom" in result
        assert "Active Story Beat" not in result

    def test_recent_event_without_stat_or_reason(self, sample_game_state: GameState):
        """System prompt handles events with no stat_name or reason."""
        sample_game_state.recent_events = [
            {"event_type": "world.location_changed", "payload": {}}
        ]
        result = build_system_prompt(sample_game_state)
        assert "world.location_changed" in result

    def test_empty_inventory_shows_empty(self):
        """System prompt shows 'Empty' for empty inventory."""
        from agentic_rpg.models.character import Character

        gs = GameState(character=Character(name="Test", profession="Rogue"))
        result = build_system_prompt(gs)
        assert "Empty" in result

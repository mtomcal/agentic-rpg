"""Tests for agent/context.py — context assembly."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agentic_rpg.models.game_state import (
    Conversation,
    GameState,
    Message,
    MessageRole,
)
from agentic_rpg.agent.context import assemble_context


class TestAssembleContext:
    """Tests for the assemble_context function."""

    def test_returns_dict_with_required_keys(self, sample_game_state: GameState):
        """assemble_context returns a dict with messages, game_state, and system_prompt."""
        result = assemble_context(sample_game_state, "I look around.")
        assert "messages" in result
        assert "game_state" in result
        assert "system_prompt" in result

    def test_messages_is_list(self, sample_game_state: GameState):
        """Messages value is a list."""
        result = assemble_context(sample_game_state, "I look around.")
        assert isinstance(result["messages"], list)

    def test_first_message_is_system(self, sample_game_state: GameState):
        """First message should be a SystemMessage with the system prompt."""
        result = assemble_context(sample_game_state, "I look around.")
        messages = result["messages"]
        assert len(messages) >= 1
        assert isinstance(messages[0], SystemMessage)

    def test_system_message_contains_game_context(self, sample_game_state: GameState):
        """System message should contain game state info like character name."""
        result = assemble_context(sample_game_state, "I look around.")
        system_msg = result["messages"][0]
        assert "Aldric" in system_msg.content

    def test_last_message_is_player_input(self, sample_game_state: GameState):
        """Last message should be a HumanMessage with the player's input."""
        result = assemble_context(sample_game_state, "I attack the goblin.")
        messages = result["messages"]
        last_msg = messages[-1]
        assert isinstance(last_msg, HumanMessage)
        assert last_msg.content == "I attack the goblin."

    def test_conversation_history_included(self, sample_game_state: GameState):
        """Conversation history messages should be included between system and player input."""
        result = assemble_context(sample_game_state, "I look around.")
        messages = result["messages"]
        # System message + history messages + player input
        # conftest sample_game_state has 3 messages in history (system, player, agent)
        # system welcome + player msg + agent msg = at least 3 history entries
        assert len(messages) >= 3  # at least system + some history + player input

    def test_player_history_becomes_human_message(self, sample_game_state: GameState):
        """Player messages in history should become HumanMessage."""
        result = assemble_context(sample_game_state, "New action.")
        messages = result["messages"]
        human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
        # At least the history player message + the new player input
        assert len(human_msgs) >= 2
        contents = [m.content for m in human_msgs]
        assert "I look around the tavern." in contents

    def test_agent_history_becomes_ai_message(self, sample_game_state: GameState):
        """Agent messages in history should become AIMessage."""
        result = assemble_context(sample_game_state, "New action.")
        messages = result["messages"]
        ai_msgs = [m for m in messages if isinstance(m, AIMessage)]
        assert len(ai_msgs) >= 1
        assert "Rusty Flagon" in ai_msgs[0].content

    def test_game_state_is_dict(self, sample_game_state: GameState):
        """game_state in result should be a serialized dict."""
        result = assemble_context(sample_game_state, "Look around.")
        assert isinstance(result["game_state"], dict)
        assert "character" in result["game_state"]
        assert "inventory" in result["game_state"]

    def test_system_prompt_is_string(self, sample_game_state: GameState):
        """system_prompt in result should be a string."""
        result = assemble_context(sample_game_state, "Look around.")
        assert isinstance(result["system_prompt"], str)
        assert len(result["system_prompt"]) > 0

    def test_window_size_limits_history(self):
        """Only the most recent window_size messages should be included."""
        from agentic_rpg.models.character import Character

        msgs = [
            Message(role=MessageRole.player, content=f"Message {i}")
            for i in range(30)
        ]
        gs = GameState(
            character=Character(name="Test", profession="Rogue"),
            conversation=Conversation(history=msgs, window_size=5),
        )
        result = assemble_context(gs, "New input.")
        messages = result["messages"]
        # Should have: system prompt + up to 5 history + player input = at most 7
        human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
        # 5 window messages are all player role + 1 new input = at most 6 HumanMessages
        assert len(human_msgs) <= 6

    def test_empty_conversation_history(self):
        """Works with no conversation history at all."""
        from agentic_rpg.models.character import Character

        gs = GameState(character=Character(name="Test", profession="Rogue"))
        result = assemble_context(gs, "Hello!")
        messages = result["messages"]
        assert len(messages) >= 2  # at least system prompt + player input
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[-1], HumanMessage)
        assert messages[-1].content == "Hello!"

    def test_conversation_summary_included(self, sample_game_state: GameState):
        """When conversation has a summary, it should appear in the system message."""
        sample_game_state.conversation.summary = "Previously, the hero explored the tavern."
        result = assemble_context(sample_game_state, "Continue.")
        system_msg = result["messages"][0]
        assert "Previously" in system_msg.content or "explored the tavern" in system_msg.content

    def test_recent_events_included_in_context(self, sample_game_state: GameState):
        """Recent events should be reflected in the system message."""
        sample_game_state.recent_events = [
            {"event_type": "character.stat_changed", "payload": {"stat_name": "health", "old_value": 100, "new_value": 80, "reason": "goblin attack"}}
        ]
        result = assemble_context(sample_game_state, "What happened?")
        system_msg = result["messages"][0]
        assert "goblin" in system_msg.content.lower() or "health" in system_msg.content.lower()

    def test_system_messages_in_history_folded(self, sample_game_state: GameState):
        """System messages from history should not create standalone SystemMessages in the middle."""
        result = assemble_context(sample_game_state, "Action.")
        messages = result["messages"]
        # Only the first message should be a SystemMessage
        for msg in messages[1:]:
            assert not isinstance(msg, SystemMessage), (
                "System messages from history should not appear as separate SystemMessages after the first"
            )

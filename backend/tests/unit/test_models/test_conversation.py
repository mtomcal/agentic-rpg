"""Tests for conversation models."""
import pytest
from datetime import datetime
from pydantic import ValidationError
from agentic_rpg.models.conversation import Message, Conversation


class TestMessage:
    """Test Message model."""

    def test_valid_message_user(self):
        """Test creating valid user message."""
        msg = Message(role="user", content="Hello, world!")
        assert msg.role == "user"
        assert msg.content == "Hello, world!"
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata is None

    def test_valid_message_assistant(self):
        """Test creating valid assistant message."""
        msg = Message(role="assistant", content="Hello!")
        assert msg.role == "assistant"
        assert msg.content == "Hello!"

    def test_valid_message_system(self):
        """Test creating valid system message."""
        msg = Message(role="system", content="System message")
        assert msg.role == "system"

    def test_valid_message_tool(self):
        """Test creating valid tool message."""
        msg = Message(role="tool", content="Tool output")
        assert msg.role == "tool"

    def test_message_with_metadata(self):
        """Test message with metadata."""
        msg = Message(
            role="user",
            content="Test",
            metadata={"session_id": "123", "custom": "data"}
        )
        assert msg.metadata["session_id"] == "123"
        assert msg.metadata["custom"] == "data"

    def test_message_with_custom_timestamp(self):
        """Test message with custom timestamp."""
        ts = datetime(2025, 1, 1, 12, 0, 0)
        msg = Message(role="user", content="Test", timestamp=ts)
        assert msg.timestamp == ts

    def test_message_content_min_length(self):
        """Test that content must be at least 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role="user", content="")
        assert "content" in str(exc_info.value)

    def test_message_invalid_role(self):
        """Test that role must be valid literal."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role="invalid", content="Test")
        # Pydantic should reject invalid role

    def test_message_json_schema_extra(self):
        """Test that JSON schema examples are defined."""
        schema = Message.model_json_schema()
        assert "examples" in schema
        assert len(schema["examples"]) > 0


class TestConversation:
    """Test Conversation model."""

    def test_empty_conversation(self):
        """Test creating empty conversation."""
        conv = Conversation()
        assert conv.messages == []
        assert conv.context == []
        assert conv.max_history == 100

    def test_conversation_with_messages(self):
        """Test conversation with initial messages."""
        msg1 = Message(role="user", content="Hello")
        msg2 = Message(role="assistant", content="Hi there!")
        conv = Conversation(messages=[msg1, msg2])
        assert len(conv.messages) == 2
        assert conv.messages[0].content == "Hello"
        assert conv.messages[1].content == "Hi there!"

    def test_conversation_with_context(self):
        """Test conversation with context."""
        conv = Conversation(context=["Important fact 1", "Important fact 2"])
        assert len(conv.context) == 2
        assert "Important fact 1" in conv.context

    def test_conversation_custom_max_history(self):
        """Test custom max_history."""
        conv = Conversation(max_history=50)
        assert conv.max_history == 50

    def test_add_message(self):
        """Test adding a message to conversation."""
        conv = Conversation()
        msg = Message(role="user", content="Test message")
        conv.add_message(msg)
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Test message"

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        conv = Conversation()
        for i in range(5):
            msg = Message(role="user", content=f"Message {i}")
            conv.add_message(msg)
        assert len(conv.messages) == 5

    def test_add_message_respects_max_history(self):
        """Test that adding messages respects max_history limit."""
        conv = Conversation(max_history=3)
        for i in range(5):
            msg = Message(role="user", content=f"Message {i}")
            conv.add_message(msg)
        assert len(conv.messages) == 3
        # Should keep the last 3 messages (2, 3, 4)
        assert conv.messages[0].content == "Message 2"
        assert conv.messages[1].content == "Message 3"
        assert conv.messages[2].content == "Message 4"

    def test_add_message_at_exact_limit(self):
        """Test adding messages at exact max_history limit."""
        conv = Conversation(max_history=3)
        for i in range(3):
            msg = Message(role="user", content=f"Message {i}")
            conv.add_message(msg)
        assert len(conv.messages) == 3
        # Add one more, should remove oldest
        msg = Message(role="user", content="Message 3")
        conv.add_message(msg)
        assert len(conv.messages) == 3
        assert conv.messages[0].content == "Message 1"

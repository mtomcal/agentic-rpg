"""Tests for Event Bus service."""
from datetime import datetime

import pytest

from agentic_rpg.services.event_bus import (
    EventBus,
    EventSchema,
    EventType,
    GameEvent,
    get_event_bus,
)


class TestEventSchema:
    """Test EventSchema validation."""

    def test_valid_payload(self):
        """Test validation with valid payload."""
        schema = EventSchema(
            type="test.event",
            required_fields={"field1", "field2"},
            optional_fields={"field3"},
        )

        payload = {"field1": "value1", "field2": "value2", "field3": "value3"}
        valid, error = schema.validate(payload)

        assert valid is True
        assert error == ""

    def test_missing_required_field(self):
        """Test validation fails when required field is missing."""
        schema = EventSchema(
            type="test.event",
            required_fields={"field1", "field2"},
        )

        payload = {"field1": "value1"}
        valid, error = schema.validate(payload)

        assert valid is False
        assert "field2" in error
        assert "Missing required fields" in error

    def test_extra_field(self):
        """Test validation fails when extra field is present."""
        schema = EventSchema(
            type="test.event",
            required_fields={"field1"},
            optional_fields={"field2"},
        )

        payload = {"field1": "value1", "field3": "value3"}
        valid, error = schema.validate(payload)

        assert valid is False
        assert "field3" in error
        assert "Unexpected fields" in error

    def test_optional_fields_allowed(self):
        """Test that optional fields are allowed but not required."""
        schema = EventSchema(
            type="test.event",
            required_fields={"field1"},
            optional_fields={"field2"},
        )

        # With optional field
        payload = {"field1": "value1", "field2": "value2"}
        valid, error = schema.validate(payload)
        assert valid is True

        # Without optional field
        payload = {"field1": "value1"}
        valid, error = schema.validate(payload)
        assert valid is True


class TestGameEvent:
    """Test GameEvent class."""

    def test_create_event(self):
        """Test creating a game event."""
        event = GameEvent(
            type="test.event",
            payload={"data": "value"},
            source="test_source",
        )

        assert event.type == "test.event"
        assert event.payload == {"data": "value"}
        assert event.source == "test_source"
        assert isinstance(event.timestamp, datetime)
        assert event.session_id is None

    def test_event_with_session(self):
        """Test creating event with session ID."""
        event = GameEvent(
            type="test.event",
            payload={},
            source="test_source",
            session_id="session123",
        )

        assert event.session_id == "session123"

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = GameEvent(
            type="test.event",
            payload={"data": "value"},
            source="test_source",
            session_id="session123",
        )

        event_dict = event.to_dict()

        assert event_dict["type"] == "test.event"
        assert event_dict["payload"] == {"data": "value"}
        assert event_dict["source"] == "test_source"
        assert event_dict["session_id"] == "session123"
        assert isinstance(event_dict["timestamp"], str)


class TestEventBus:
    """Test EventBus functionality."""

    @pytest.fixture
    def event_bus(self):
        """Create a fresh event bus for each test."""
        return EventBus()

    def test_publish_event(self, event_bus):
        """Test publishing an event."""
        event = GameEvent(
            type="test.event",
            payload={"data": "value"},
            source="test_source",
        )

        # Should not raise
        event_bus.publish(event)

    def test_subscribe_and_publish(self, event_bus):
        """Test subscribing to and receiving events."""
        received_events = []

        def callback(event: GameEvent):
            received_events.append(event)

        event_bus.subscribe("test.event", callback)

        event = GameEvent(
            type="test.event",
            payload={"data": "value"},
            source="test_source",
        )

        event_bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].type == "test.event"
        assert received_events[0].payload == {"data": "value"}

    def test_multiple_subscribers(self, event_bus):
        """Test multiple subscribers receive the same event."""
        received1 = []
        received2 = []

        def callback1(event: GameEvent):
            received1.append(event)

        def callback2(event: GameEvent):
            received2.append(event)

        event_bus.subscribe("test.event", callback1)
        event_bus.subscribe("test.event", callback2)

        event = GameEvent(
            type="test.event",
            payload={"data": "value"},
            source="test_source",
        )

        event_bus.publish(event)

        assert len(received1) == 1
        assert len(received2) == 1
        assert received1[0].payload == received2[0].payload

    def test_unsubscribe(self, event_bus):
        """Test unsubscribing from events."""
        received_events = []

        def callback(event: GameEvent):
            received_events.append(event)

        event_bus.subscribe("test.event", callback)
        event_bus.unsubscribe("test.event", callback)

        event = GameEvent(
            type="test.event",
            payload={"data": "value"},
            source="test_source",
        )

        event_bus.publish(event)

        assert len(received_events) == 0

    def test_event_type_filter(self, event_bus):
        """Test that subscribers only receive their event type."""
        received_a = []
        received_b = []

        def callback_a(event: GameEvent):
            received_a.append(event)

        def callback_b(event: GameEvent):
            received_b.append(event)

        event_bus.subscribe("event.a", callback_a)
        event_bus.subscribe("event.b", callback_b)

        event_a = GameEvent(type="event.a", payload={}, source="test")
        event_b = GameEvent(type="event.b", payload={}, source="test")

        event_bus.publish(event_a)
        event_bus.publish(event_b)

        assert len(received_a) == 1
        assert len(received_b) == 1
        assert received_a[0].type == "event.a"
        assert received_b[0].type == "event.b"

    def test_register_schema(self, event_bus):
        """Test registering and validating event schema."""
        schema = EventSchema(
            type="test.event",
            required_fields={"field1"},
        )

        event_bus.register_schema(schema)

        # Valid event should publish
        valid_event = GameEvent(
            type="test.event",
            payload={"field1": "value"},
            source="test",
        )
        event_bus.publish(valid_event)

        # Invalid event should raise
        invalid_event = GameEvent(
            type="test.event",
            payload={"wrong_field": "value"},
            source="test",
        )

        with pytest.raises(ValueError, match="Invalid event payload"):
            event_bus.publish(invalid_event)

    def test_event_history(self, event_bus):
        """Test event history tracking."""
        events = [
            GameEvent(type="event.a", payload={}, source="test"),
            GameEvent(type="event.b", payload={}, source="test"),
            GameEvent(type="event.a", payload={}, source="test"),
        ]

        for event in events:
            event_bus.publish(event)

        history = event_bus.get_history()
        assert len(history) == 3

    def test_event_history_filter_by_type(self, event_bus):
        """Test filtering event history by type."""
        events = [
            GameEvent(type="event.a", payload={}, source="test"),
            GameEvent(type="event.b", payload={}, source="test"),
            GameEvent(type="event.a", payload={}, source="test"),
        ]

        for event in events:
            event_bus.publish(event)

        history_a = event_bus.get_history(event_type="event.a")
        assert len(history_a) == 2
        assert all(e.type == "event.a" for e in history_a)

    def test_event_history_filter_by_session(self, event_bus):
        """Test filtering event history by session ID."""
        events = [
            GameEvent(type="event.a", payload={}, source="test", session_id="session1"),
            GameEvent(type="event.b", payload={}, source="test", session_id="session2"),
            GameEvent(type="event.a", payload={}, source="test", session_id="session1"),
        ]

        for event in events:
            event_bus.publish(event)

        history_s1 = event_bus.get_history(session_id="session1")
        assert len(history_s1) == 2
        assert all(e.session_id == "session1" for e in history_s1)

    def test_event_history_limit(self, event_bus):
        """Test limiting event history results."""
        events = [
            GameEvent(type="event.a", payload={}, source="test")
            for _ in range(10)
        ]

        for event in events:
            event_bus.publish(event)

        history = event_bus.get_history(limit=5)
        assert len(history) == 5

    def test_event_history_max_size(self, event_bus):
        """Test that history is limited to max size."""
        # Event bus has max_history of 1000
        for i in range(1100):
            event = GameEvent(type="test.event", payload={"i": i}, source="test")
            event_bus.publish(event)

        history = event_bus.get_history(limit=2000)
        assert len(history) == 1000

    def test_subscriber_error_handling(self, event_bus):
        """Test that errors in subscribers don't stop event processing."""
        received = []

        def bad_callback(event: GameEvent):
            raise Exception("Subscriber error")

        def good_callback(event: GameEvent):
            received.append(event)

        event_bus.subscribe("test.event", bad_callback)
        event_bus.subscribe("test.event", good_callback)

        event = GameEvent(type="test.event", payload={}, source="test")
        event_bus.publish(event)

        # Good callback should still receive the event
        assert len(received) == 1


class TestEventType:
    """Test EventType enum."""

    def test_event_types_defined(self):
        """Test that standard event types are defined."""
        assert EventType.STATE_UPDATED == "state.updated"
        assert EventType.GAME_CREATED == "game.created"
        assert EventType.ITEM_ACQUIRED == "inventory.item_acquired"
        assert EventType.LOCATION_CHANGED == "world.location_changed"


class TestGetEventBus:
    """Test global event bus singleton."""

    def test_get_event_bus_returns_same_instance(self):
        """Test that get_event_bus returns the same instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_get_event_bus_is_event_bus(self):
        """Test that get_event_bus returns an EventBus instance."""
        bus = get_event_bus()
        assert isinstance(bus, EventBus)

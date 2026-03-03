"""Tests for the async EventBus — publish, subscribe, unsubscribe, history."""

import asyncio
from uuid import uuid4

import pytest

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.events import GameEvent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(
    event_type: str = "character.stat_changed",
    session_id=None,
    source: str = "test",
    payload: dict | None = None,
) -> GameEvent:
    return GameEvent(
        event_type=event_type,
        payload=payload or {"stat_name": "health", "old_value": 100, "new_value": 80},
        source=source,
        session_id=session_id or uuid4(),
    )


# ===========================================================================
# Subscribe
# ===========================================================================

class TestSubscribe:
    """EventBus.subscribe registers callbacks and returns a subscription ID."""

    def test_subscribe_returns_subscription_id(self, event_bus: EventBus):
        """subscribe() should return a non-empty string subscription ID."""

        async def noop(event: GameEvent) -> None:
            pass

        sub_id = event_bus.subscribe("character.stat_changed", noop)
        assert isinstance(sub_id, str)
        assert len(sub_id) > 0

    def test_subscribe_multiple_to_same_type(self, event_bus: EventBus):
        """Multiple callbacks can subscribe to the same event type."""

        async def cb1(event: GameEvent) -> None:
            pass

        async def cb2(event: GameEvent) -> None:
            pass

        id1 = event_bus.subscribe("character.stat_changed", cb1)
        id2 = event_bus.subscribe("character.stat_changed", cb2)
        assert id1 != id2

    def test_subscribe_different_types(self, event_bus: EventBus):
        """Subscribing to different event types returns different IDs."""

        async def cb(event: GameEvent) -> None:
            pass

        id1 = event_bus.subscribe("character.stat_changed", cb)
        id2 = event_bus.subscribe("world.location_changed", cb)
        assert id1 != id2

    def test_subscribe_ids_are_globally_unique(self, event_bus: EventBus):
        """Subscription IDs must be unique across all event types and callbacks."""

        async def noop(event: GameEvent) -> None:
            pass

        id1 = event_bus.subscribe("character.stat_changed", noop)
        id2 = event_bus.subscribe("character.stat_changed", noop)
        id3 = event_bus.subscribe("world.location_changed", noop)

        assert len({id1, id2, id3}) == 3


# ===========================================================================
# Publish
# ===========================================================================

class TestPublish:
    """EventBus.publish dispatches events to matching subscribers."""

    async def test_publish_calls_subscriber(self, event_bus: EventBus):
        """Publishing an event invokes the subscribed callback with the event."""
        received: list[GameEvent] = []

        async def handler(event: GameEvent) -> None:
            received.append(event)

        event_bus.subscribe("character.stat_changed", handler)
        event = _make_event("character.stat_changed")
        await event_bus.publish(event)

        assert len(received) == 1
        assert received[0].event_id == event.event_id
        assert received[0].event_type == "character.stat_changed"

    async def test_publish_only_notifies_matching_subscribers(self, event_bus: EventBus):
        """Subscribers only receive events of their subscribed type."""
        stat_events: list[GameEvent] = []
        location_events: list[GameEvent] = []

        async def stat_handler(event: GameEvent) -> None:
            stat_events.append(event)

        async def location_handler(event: GameEvent) -> None:
            location_events.append(event)

        event_bus.subscribe("character.stat_changed", stat_handler)
        event_bus.subscribe("world.location_changed", location_handler)

        await event_bus.publish(_make_event("character.stat_changed"))

        assert len(stat_events) == 1
        assert len(location_events) == 0

    async def test_publish_multiple_subscribers(self, event_bus: EventBus):
        """Multiple subscribers for the same type all receive the event."""
        received_a: list[GameEvent] = []
        received_b: list[GameEvent] = []

        async def handler_a(event: GameEvent) -> None:
            received_a.append(event)

        async def handler_b(event: GameEvent) -> None:
            received_b.append(event)

        event_bus.subscribe("character.stat_changed", handler_a)
        event_bus.subscribe("character.stat_changed", handler_b)

        event = _make_event("character.stat_changed")
        await event_bus.publish(event)

        assert len(received_a) == 1
        assert len(received_b) == 1
        assert received_a[0].event_id == event.event_id
        assert received_b[0].event_id == event.event_id

    async def test_publish_no_subscribers_does_not_raise(self, event_bus: EventBus):
        """Publishing with no subscribers should not raise."""
        event = _make_event("unknown.event")
        await event_bus.publish(event)  # should not raise

    async def test_publish_subscriber_error_does_not_block_others(
        self, event_bus: EventBus
    ):
        """A failing subscriber should not prevent other subscribers from receiving."""
        received: list[GameEvent] = []

        async def bad_handler(event: GameEvent) -> None:
            raise RuntimeError("subscriber error")

        async def good_handler(event: GameEvent) -> None:
            received.append(event)

        event_bus.subscribe("character.stat_changed", bad_handler)
        event_bus.subscribe("character.stat_changed", good_handler)

        event = _make_event("character.stat_changed")
        await event_bus.publish(event)

        assert len(received) == 1
        assert received[0].event_id == event.event_id

    async def test_publish_all_subscribers_raise_does_not_propagate(
        self, event_bus: EventBus
    ):
        """If all subscribers raise, publish should still complete without raising."""

        async def bad1(event: GameEvent) -> None:
            raise ValueError("bad1")

        async def bad2(event: GameEvent) -> None:
            raise RuntimeError("bad2")

        event_bus.subscribe("character.stat_changed", bad1)
        event_bus.subscribe("character.stat_changed", bad2)

        event = _make_event("character.stat_changed")
        await event_bus.publish(event)  # must not raise

        # Event should still be stored in history despite subscriber failures
        history = await event_bus.get_history()
        assert len(history) == 1
        assert history[0].event_id == event.event_id

    async def test_publish_preserves_event_payload(self, event_bus: EventBus):
        """Event payload must be identical from publish to subscriber."""
        received: list[GameEvent] = []

        async def handler(event: GameEvent) -> None:
            received.append(event)

        event_bus.subscribe("character.stat_changed", handler)

        payload = {"stat_name": "health", "old_value": 100, "new_value": 75, "reason": "poison"}
        event = _make_event("character.stat_changed", payload=payload)
        await event_bus.publish(event)

        assert len(received) == 1
        assert received[0].payload == payload
        assert received[0].source == "test"


# ===========================================================================
# Unsubscribe
# ===========================================================================

class TestUnsubscribe:
    """EventBus.unsubscribe removes a subscription by ID."""

    async def test_unsubscribe_stops_delivery(self, event_bus: EventBus):
        """After unsubscribe, the callback should no longer be invoked."""
        received: list[GameEvent] = []

        async def handler(event: GameEvent) -> None:
            received.append(event)

        sub_id = event_bus.subscribe("character.stat_changed", handler)
        event_bus.unsubscribe(sub_id)

        await event_bus.publish(_make_event("character.stat_changed"))
        assert len(received) == 0

    def test_unsubscribe_unknown_id_does_not_raise(self, event_bus: EventBus):
        """Unsubscribing with an unknown ID should be a no-op."""
        event_bus.unsubscribe("nonexistent-id")  # should not raise

    async def test_unsubscribe_one_keeps_others(self, event_bus: EventBus):
        """Unsubscribing one callback does not affect other subscribers."""
        received_a: list[GameEvent] = []
        received_b: list[GameEvent] = []

        async def handler_a(event: GameEvent) -> None:
            received_a.append(event)

        async def handler_b(event: GameEvent) -> None:
            received_b.append(event)

        id_a = event_bus.subscribe("character.stat_changed", handler_a)
        event_bus.subscribe("character.stat_changed", handler_b)

        event_bus.unsubscribe(id_a)
        await event_bus.publish(_make_event("character.stat_changed"))

        assert len(received_a) == 0
        assert len(received_b) == 1

    async def test_unsubscribe_same_id_twice_is_idempotent(self, event_bus: EventBus):
        """Unsubscribing the same ID twice should not raise."""
        received: list[GameEvent] = []

        async def handler(event: GameEvent) -> None:
            received.append(event)

        sub_id = event_bus.subscribe("character.stat_changed", handler)
        event_bus.unsubscribe(sub_id)
        event_bus.unsubscribe(sub_id)  # second call is no-op

        await event_bus.publish(_make_event("character.stat_changed"))
        assert len(received) == 0


# ===========================================================================
# History
# ===========================================================================

class TestGetHistory:
    """EventBus.get_history returns stored events with optional filtering."""

    async def test_history_stores_published_events(self, event_bus: EventBus):
        """Published events should appear in the history."""
        event = _make_event("character.stat_changed")
        await event_bus.publish(event)

        history = await event_bus.get_history()
        assert len(history) == 1
        assert history[0].event_id == event.event_id

    async def test_history_empty_initially(self, event_bus: EventBus):
        """History should be empty before any events are published."""
        history = await event_bus.get_history()
        assert len(history) == 0

    async def test_history_filter_by_event_type(self, event_bus: EventBus):
        """get_history(event_type=...) should only return matching events."""
        session_id = uuid4()
        await event_bus.publish(
            _make_event("character.stat_changed", session_id=session_id)
        )
        await event_bus.publish(
            _make_event("world.location_changed", session_id=session_id)
        )
        await event_bus.publish(
            _make_event("character.stat_changed", session_id=session_id)
        )

        history = await event_bus.get_history(event_type="character.stat_changed")
        assert len(history) == 2
        assert all(e.event_type == "character.stat_changed" for e in history)

    async def test_history_filter_by_session_id(self, event_bus: EventBus):
        """get_history(session_id=...) should only return events for that session."""
        session_a = uuid4()
        session_b = uuid4()

        await event_bus.publish(_make_event(session_id=session_a))
        await event_bus.publish(_make_event(session_id=session_b))
        await event_bus.publish(_make_event(session_id=session_a))

        history = await event_bus.get_history(session_id=session_a)
        assert len(history) == 2
        assert all(e.session_id == session_a for e in history)

    async def test_history_filter_by_type_and_session(self, event_bus: EventBus):
        """Combined filter by type AND session_id."""
        session = uuid4()
        await event_bus.publish(
            _make_event("character.stat_changed", session_id=session)
        )
        await event_bus.publish(
            _make_event("world.location_changed", session_id=session)
        )
        await event_bus.publish(_make_event("character.stat_changed"))  # different session

        history = await event_bus.get_history(
            event_type="character.stat_changed", session_id=session
        )
        assert len(history) == 1
        assert history[0].event_type == "character.stat_changed"
        assert history[0].session_id == session

    async def test_history_respects_limit(self, event_bus: EventBus):
        """get_history(limit=N) should return at most N events."""
        for _ in range(10):
            await event_bus.publish(_make_event())

        history = await event_bus.get_history(limit=5)
        assert len(history) == 5

    async def test_history_bounded_by_history_limit(self):
        """The deque should evict old events when history_limit is exceeded."""
        bus = EventBus(history_limit=3)

        events = []
        for i in range(5):
            e = _make_event()
            events.append(e)
            await bus.publish(e)

        history = await bus.get_history()
        assert len(history) == 3
        # Should contain the 3 most recent events
        history_ids = {e.event_id for e in history}
        assert events[2].event_id in history_ids
        assert events[3].event_id in history_ids
        assert events[4].event_id in history_ids
        # Old ones evicted
        assert events[0].event_id not in history_ids
        assert events[1].event_id not in history_ids

    async def test_history_maintains_insertion_order(self, event_bus: EventBus):
        """History returns events in the order they were published."""
        session = uuid4()
        e1 = _make_event(session_id=session)
        e2 = _make_event(session_id=session)

        await event_bus.publish(e1)
        await event_bus.publish(e2)

        history = await event_bus.get_history()
        assert len(history) == 2
        assert history[0].event_id == e1.event_id
        assert history[1].event_id == e2.event_id

    async def test_history_nonexistent_type_returns_empty(self, event_bus: EventBus):
        """Filtering by non-existent event type returns empty list."""
        await event_bus.publish(_make_event("character.stat_changed"))

        history = await event_bus.get_history(event_type="never.happens")
        assert history == []

    async def test_history_nonexistent_session_returns_empty(self, event_bus: EventBus):
        """Filtering by non-existent session ID returns empty list."""
        await event_bus.publish(_make_event())

        history = await event_bus.get_history(session_id=uuid4())
        assert history == []

    async def test_history_limit_greater_than_available(self, event_bus: EventBus):
        """limit > available events returns all available events."""
        for _ in range(3):
            await event_bus.publish(_make_event())

        history = await event_bus.get_history(limit=100)
        assert len(history) == 3

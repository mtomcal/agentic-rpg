"""Tests for EventPersistence — save, load, query events from the database."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import asyncpg
import pytest

from agentic_rpg.events.persistence import EventPersistence
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


# ---------------------------------------------------------------------------
# Fixture: event_persistence with a seeded session
# ---------------------------------------------------------------------------

@pytest.fixture
async def persistence(seeded_session) -> EventPersistence:
    """Return an EventPersistence instance backed by the test DB pool."""
    return EventPersistence(seeded_session["pool"])


# ===========================================================================
# save_event
# ===========================================================================

class TestSaveEvent:
    """EventPersistence.save_event writes an event row to the events table."""

    async def test_save_event_inserts_row(self, persistence: EventPersistence, seeded_session):
        """Saving an event should insert a row that can be fetched back."""
        session_id = seeded_session["session_id"]
        event = _make_event(session_id=session_id)

        await persistence.save_event(event)

        # Verify via raw SQL
        pool = seeded_session["pool"]
        row = await pool.fetchrow(
            "SELECT id, type, payload, source, session_id FROM events WHERE id = $1",
            event.event_id,
        )
        assert row is not None, "Event row should exist in database"
        assert row["id"] == event.event_id
        assert row["type"] == "character.stat_changed"
        assert row["source"] == "test"
        assert row["session_id"] == session_id

    async def test_save_event_stores_payload_as_jsonb(self, persistence, seeded_session):
        """Event payload should be stored as JSONB and round-trip correctly."""
        session_id = seeded_session["session_id"]
        payload = {"stat_name": "energy", "old_value": 50.0, "new_value": 30.0, "reason": "magic"}
        event = _make_event(session_id=session_id, payload=payload)

        await persistence.save_event(event)

        pool = seeded_session["pool"]
        row = await pool.fetchrow("SELECT payload FROM events WHERE id = $1", event.event_id)
        import json
        stored_payload = json.loads(row["payload"])
        assert stored_payload["stat_name"] == "energy"
        assert stored_payload["old_value"] == 50.0
        assert stored_payload["new_value"] == 30.0
        assert stored_payload["reason"] == "magic"

    async def test_save_event_stores_timestamp(self, persistence, seeded_session):
        """Event timestamp (created_at) should be persisted."""
        session_id = seeded_session["session_id"]
        event = _make_event(session_id=session_id)

        await persistence.save_event(event)

        pool = seeded_session["pool"]
        row = await pool.fetchrow("SELECT created_at FROM events WHERE id = $1", event.event_id)
        assert row is not None, "Event row should exist"
        # created_at should be close to the event's timestamp
        assert abs((row["created_at"].replace(tzinfo=UTC) - event.timestamp.replace(tzinfo=UTC)).total_seconds()) < 5
        # Verify timestamp is recent (within last 10 seconds)
        time_diff = (datetime.now(UTC) - row["created_at"].replace(tzinfo=UTC)).total_seconds()
        assert 0 <= time_diff < 10

    async def test_save_multiple_events(self, persistence, seeded_session):
        """Multiple events can be saved for the same session."""
        session_id = seeded_session["session_id"]
        e1 = _make_event(session_id=session_id, event_type="character.stat_changed")
        e2 = _make_event(session_id=session_id, event_type="world.location_changed")

        await persistence.save_event(e1)
        await persistence.save_event(e2)

        pool = seeded_session["pool"]
        count = await pool.fetchval(
            "SELECT COUNT(*) FROM events WHERE session_id = $1", session_id
        )
        assert count == 2


# ===========================================================================
# get_event_by_id
# ===========================================================================

class TestGetEventById:
    """EventPersistence.get_event_by_id retrieves a single event."""

    async def test_get_event_by_id_returns_event(self, persistence, seeded_session):
        """Should return the saved event with all fields intact."""
        session_id = seeded_session["session_id"]
        event = _make_event(session_id=session_id)
        await persistence.save_event(event)

        result = await persistence.get_event_by_id(event.event_id)
        assert result is not None, "Event should be found by ID"
        assert result.event_id == event.event_id
        assert result.event_type == "character.stat_changed"
        assert result.source == "test"
        assert result.session_id == session_id
        assert result.payload["stat_name"] == "health"

    async def test_get_event_by_id_not_found(self, persistence):
        """Should return None for a non-existent event ID."""
        result = await persistence.get_event_by_id(uuid4())
        assert result is None, "Non-existent event should return None"


# ===========================================================================
# get_events_for_session
# ===========================================================================

class TestGetEventsForSession:
    """EventPersistence.get_events_for_session returns events for a session."""

    async def test_returns_events_for_session(self, persistence, seeded_session):
        """Should return all events belonging to the given session."""
        session_id = seeded_session["session_id"]
        e1 = _make_event(session_id=session_id, event_type="character.stat_changed")
        e2 = _make_event(session_id=session_id, event_type="world.location_changed")
        await persistence.save_event(e1)
        await persistence.save_event(e2)

        events = await persistence.get_events_for_session(session_id)
        assert len(events) == 2
        event_ids = {e.event_id for e in events}
        assert e1.event_id in event_ids
        assert e2.event_id in event_ids

    async def test_returns_empty_for_unknown_session(self, persistence):
        """Should return an empty list for a session with no events."""
        events = await persistence.get_events_for_session(uuid4())
        assert events == []

    async def test_respects_limit(self, persistence, seeded_session):
        """Should return at most `limit` events."""
        session_id = seeded_session["session_id"]
        for _ in range(5):
            await persistence.save_event(_make_event(session_id=session_id))

        events = await persistence.get_events_for_session(session_id, limit=3)
        assert len(events) == 3

    async def test_ordered_by_created_at_desc(self, persistence, seeded_session):
        """Events should be returned newest first."""
        session_id = seeded_session["session_id"]
        e1 = _make_event(session_id=session_id)
        await persistence.save_event(e1)
        # Small delay to ensure ordering
        await asyncio.sleep(0.01)
        e2 = _make_event(session_id=session_id)
        await persistence.save_event(e2)

        events = await persistence.get_events_for_session(session_id)
        assert len(events) == 2
        # Newest first
        assert events[0].event_id == e2.event_id
        assert events[1].event_id == e1.event_id


# ===========================================================================
# get_events_by_type
# ===========================================================================

class TestGetEventsByType:
    """EventPersistence.get_events_by_type filters events within a session."""

    async def test_filters_by_type(self, persistence, seeded_session):
        """Should return only events matching the given type."""
        session_id = seeded_session["session_id"]
        e1 = _make_event(session_id=session_id, event_type="character.stat_changed")
        e2 = _make_event(session_id=session_id, event_type="world.location_changed")
        e3 = _make_event(session_id=session_id, event_type="character.stat_changed")
        await persistence.save_event(e1)
        await persistence.save_event(e2)
        await persistence.save_event(e3)

        events = await persistence.get_events_by_type(session_id, "character.stat_changed")
        assert len(events) == 2
        assert all(e.event_type == "character.stat_changed" for e in events)

    async def test_returns_empty_for_no_matching_type(self, persistence, seeded_session):
        """Should return empty list when no events match the type."""
        session_id = seeded_session["session_id"]
        await persistence.save_event(_make_event(session_id=session_id, event_type="character.stat_changed"))

        events = await persistence.get_events_by_type(session_id, "never.happens")
        assert events == []

    async def test_respects_limit(self, persistence, seeded_session):
        """Should return at most `limit` events."""
        session_id = seeded_session["session_id"]
        for _ in range(5):
            await persistence.save_event(
                _make_event(session_id=session_id, event_type="character.stat_changed")
            )

        events = await persistence.get_events_by_type(session_id, "character.stat_changed", limit=2)
        assert len(events) == 2


# ===========================================================================
# get_events_by_time_range
# ===========================================================================

class TestGetEventsByTimeRange:
    """EventPersistence.get_events_by_time_range filters by timestamp."""

    async def test_returns_events_within_range(self, persistence, seeded_session):
        """Should return events whose timestamp falls within the range."""
        session_id = seeded_session["session_id"]
        start_time = datetime.now(UTC)

        e1 = _make_event(session_id=session_id)
        await persistence.save_event(e1)
        await asyncio.sleep(0.01)

        end_time = datetime.now(UTC) + timedelta(seconds=1)

        events = await persistence.get_events_by_time_range(session_id, start_time, end_time)
        assert len(events) == 1
        assert events[0].event_id == e1.event_id

    async def test_excludes_events_outside_range(self, persistence, seeded_session):
        """Events outside the time range should not be returned."""
        session_id = seeded_session["session_id"]

        await persistence.save_event(_make_event(session_id=session_id))

        # Query a range in the far future
        future_start = datetime.now(UTC) + timedelta(hours=1)
        future_end = datetime.now(UTC) + timedelta(hours=2)

        events = await persistence.get_events_by_time_range(session_id, future_start, future_end)
        assert events == []

    async def test_respects_limit(self, persistence, seeded_session):
        """Should return at most `limit` events."""
        session_id = seeded_session["session_id"]
        start_time = datetime.now(UTC) - timedelta(seconds=1)

        for _ in range(5):
            await persistence.save_event(_make_event(session_id=session_id))

        end_time = datetime.now(UTC) + timedelta(seconds=1)

        events = await persistence.get_events_by_time_range(
            session_id, start_time, end_time, limit=2
        )
        assert len(events) == 2


# ===========================================================================
# delete_events_for_session
# ===========================================================================

class TestDeleteEventsForSession:
    """EventPersistence.delete_events_for_session removes all events for a session."""

    async def test_deletes_all_events(self, persistence, seeded_session):
        """Should delete all events for the given session and return the count."""
        session_id = seeded_session["session_id"]
        await persistence.save_event(_make_event(session_id=session_id))
        await persistence.save_event(_make_event(session_id=session_id))
        await persistence.save_event(_make_event(session_id=session_id))

        deleted = await persistence.delete_events_for_session(session_id)
        assert deleted == 3

        # Verify they're gone
        events = await persistence.get_events_for_session(session_id)
        assert events == []

    async def test_returns_zero_for_no_events(self, persistence):
        """Should return 0 when no events exist for the session."""
        deleted = await persistence.delete_events_for_session(uuid4())
        assert deleted == 0

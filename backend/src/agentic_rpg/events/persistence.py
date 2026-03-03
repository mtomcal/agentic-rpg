"""Event persistence — save and query GameEvents in PostgreSQL."""

import json
from datetime import UTC, datetime
from uuid import UUID

import asyncpg

from agentic_rpg.models.events import GameEvent


class EventPersistence:
    """Persists GameEvents to the PostgreSQL events table."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def save_event(self, event: GameEvent) -> None:
        """Insert a GameEvent into the events table."""
        await self._pool.execute(
            """INSERT INTO events (id, session_id, type, payload, source, created_at)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            event.event_id,
            event.session_id,
            event.event_type,
            json.dumps(event.payload),
            event.source,
            event.timestamp,
        )

    async def get_event_by_id(self, event_id: UUID) -> GameEvent | None:
        """Retrieve a single event by its ID, or None if not found."""
        row = await self._pool.fetchrow(
            "SELECT id, session_id, type, payload, source, created_at FROM events WHERE id = $1",
            event_id,
        )
        if row is None:
            return None
        return self._row_to_event(row)

    async def get_events_for_session(
        self, session_id: UUID, limit: int = 100
    ) -> list[GameEvent]:
        """Return events for a session, newest first."""
        rows = await self._pool.fetch(
            """SELECT id, session_id, type, payload, source, created_at
               FROM events
               WHERE session_id = $1
               ORDER BY created_at DESC
               LIMIT $2""",
            session_id,
            limit,
        )
        return [self._row_to_event(r) for r in rows]

    async def get_events_by_type(
        self, session_id: UUID, event_type: str, limit: int = 100
    ) -> list[GameEvent]:
        """Return events of a specific type within a session, newest first."""
        rows = await self._pool.fetch(
            """SELECT id, session_id, type, payload, source, created_at
               FROM events
               WHERE session_id = $1 AND type = $2
               ORDER BY created_at DESC
               LIMIT $3""",
            session_id,
            event_type,
            limit,
        )
        return [self._row_to_event(r) for r in rows]

    async def get_events_by_time_range(
        self,
        session_id: UUID,
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> list[GameEvent]:
        """Return events within a time range for a session, newest first."""
        rows = await self._pool.fetch(
            """SELECT id, session_id, type, payload, source, created_at
               FROM events
               WHERE session_id = $1 AND created_at >= $2 AND created_at <= $3
               ORDER BY created_at DESC
               LIMIT $4""",
            session_id,
            start,
            end,
            limit,
        )
        return [self._row_to_event(r) for r in rows]

    async def delete_events_for_session(self, session_id: UUID) -> int:
        """Delete all events for a session. Returns the number of rows deleted."""
        result = await self._pool.execute(
            "DELETE FROM events WHERE session_id = $1", session_id
        )
        # asyncpg returns e.g. "DELETE 3"
        return int(result.split()[-1])

    @staticmethod
    def _row_to_event(row: asyncpg.Record) -> GameEvent:
        """Convert a database row to a GameEvent."""
        payload = row["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return GameEvent(
            event_id=row["id"],
            event_type=row["type"],
            payload=payload,
            source=row["source"],
            session_id=row["session_id"],
            timestamp=row["created_at"],
        )

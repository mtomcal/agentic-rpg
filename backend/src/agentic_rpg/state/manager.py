"""Game state manager — CRUD operations on game sessions."""

from datetime import UTC, datetime
from uuid import UUID

import asyncpg

from agentic_rpg.models.game_state import GameState, SessionStatus


class StateManager:
    """Manages game state persistence via asyncpg."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create_session(self, state: GameState) -> GameState:
        """Create a new game session, persisting the full state to the DB.

        Inserts a player row if one doesn't exist, then inserts the session.
        Raises on duplicate session_id.
        """
        session = state.session
        game_state_json = state.model_dump_json()

        # Upsert player row
        await self._pool.execute(
            "INSERT INTO players (id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
            session.player_id,
        )
        # Insert session
        await self._pool.execute(
            """INSERT INTO sessions (id, player_id, status, genre, schema_version, game_state, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8)""",
            session.session_id,
            session.player_id,
            session.status.value,
            "fantasy",
            str(session.schema_version),
            game_state_json,
            session.created_at,
            session.updated_at,
        )

        return state

    async def load_game_state(self, session_id: UUID) -> GameState | None:
        """Load the full game state for a session. Returns None if not found."""
        row = await self._pool.fetchrow(
            "SELECT game_state FROM sessions WHERE id = $1",
            session_id,
        )
        if row is None:
            return None
        return GameState.model_validate_json(row["game_state"])

    async def save_game_state(self, state: GameState) -> None:
        """Persist the full game state, updating the existing session row.

        Raises if the session does not exist.
        """
        state.session.updated_at = datetime.now(UTC)
        game_state_json = state.model_dump_json()

        result = await self._pool.execute(
            """UPDATE sessions
               SET game_state = $1::jsonb,
                   status = $2,
                   updated_at = $3
               WHERE id = $4""",
            game_state_json,
            state.session.status.value,
            state.session.updated_at,
            state.session.session_id,
        )
        # asyncpg returns "UPDATE N" where N is affected rows
        if result == "UPDATE 0":
            raise ValueError(
                f"Session {state.session.session_id} not found — cannot save"
            )

    async def delete_game_state(self, session_id: UUID) -> bool:
        """Delete a session. Returns True if deleted, False if not found."""
        result = await self._pool.execute(
            "DELETE FROM sessions WHERE id = $1",
            session_id,
        )
        return result == "DELETE 1"

    async def list_sessions(self, player_id: UUID) -> list[GameState]:
        """List all game states for a given player."""
        rows = await self._pool.fetch(
            "SELECT game_state FROM sessions WHERE player_id = $1 ORDER BY created_at",
            player_id,
        )
        return [GameState.model_validate_json(row["game_state"]) for row in rows]

    async def update_session_status(
        self, session_id: UUID, status: SessionStatus
    ) -> None:
        """Update only the session status. Raises if session not found."""
        # Update status in both the row column and the JSONB state
        result = await self._pool.execute(
            """UPDATE sessions
               SET status = $1,
                   game_state = jsonb_set(game_state, '{session,status}', to_jsonb($1::text)),
                   updated_at = now()
               WHERE id = $2""",
            status.value,
            session_id,
        )
        if result == "UPDATE 0":
            raise ValueError(f"Session {session_id} not found — cannot update status")

"""FastAPI dependency injection functions."""

from uuid import UUID

from fastapi import Header, HTTPException, Request

from agentic_rpg.state.manager import StateManager


async def get_db_pool(request: Request):
    """Extract the asyncpg pool from app state."""
    return request.app.state.db_pool


async def get_state_manager(request: Request) -> StateManager:
    """Build a StateManager from the app's DB pool."""
    pool = request.app.state.db_pool
    return StateManager(pool)


async def get_current_player(
    x_player_id: str | None = Header(None),
) -> UUID:
    """Extract and validate the X-Player-ID header."""
    if x_player_id is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "Missing X-Player-ID header"},
        )
    try:
        return UUID(x_player_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid X-Player-ID header — must be a valid UUID"},
        )

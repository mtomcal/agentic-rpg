"""HTTP handler functions for session management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from agentic_rpg.api.dependencies import get_current_player, get_state_manager
from agentic_rpg.models.api import (
    DeleteResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionSummary,
)
from agentic_rpg.models.character import Character
from agentic_rpg.models.game_state import GameState, Session, SessionStatus
from agentic_rpg.state.manager import StateManager

router = APIRouter(prefix="/api/v1", tags=["sessions"])


@router.post("/sessions", status_code=201)
async def create_session(
    body: SessionCreateRequest,
    player_id: UUID = Depends(get_current_player),
    state_manager: StateManager = Depends(get_state_manager),
) -> SessionCreateResponse:
    """Create a new game session."""
    # Build initial game state from the request
    game_state = GameState(
        session=Session(
            player_id=player_id,
            status=SessionStatus.active,
        ),
        character=Character(
            name=body.character.name,
            profession=body.character.profession,
            background=body.character.background,
        ),
    )
    created = await state_manager.create_session(game_state)
    return SessionCreateResponse(
        session_id=created.session.session_id,
        game_state=created,
    )


@router.get("/sessions")
async def list_sessions(
    player_id: UUID = Depends(get_current_player),
    state_manager: StateManager = Depends(get_state_manager),
) -> SessionListResponse:
    """List all sessions for the current player."""
    states = await state_manager.list_sessions(player_id)
    summaries = [
        SessionSummary(
            session_id=gs.session.session_id,
            character_name=gs.character.name,
            genre="",
            status=gs.session.status.value,
            created_at=gs.session.created_at.isoformat(),
            updated_at=gs.session.updated_at.isoformat(),
        )
        for gs in states
    ]
    return SessionListResponse(sessions=summaries)


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: UUID,
    player_id: UUID = Depends(get_current_player),
    state_manager: StateManager = Depends(get_state_manager),
) -> SessionDetailResponse:
    """Get the full game state for a session."""
    game_state = await state_manager.load_game_state(session_id)
    if game_state is None:
        raise HTTPException(status_code=404, detail={"error": "session_not_found"})
    return SessionDetailResponse(game_state=game_state)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    player_id: UUID = Depends(get_current_player),
    state_manager: StateManager = Depends(get_state_manager),
) -> DeleteResponse:
    """Delete a game session."""
    deleted = await state_manager.delete_game_state(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"error": "session_not_found"})
    return DeleteResponse(success=True)

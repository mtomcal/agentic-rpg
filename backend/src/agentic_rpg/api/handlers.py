"""HTTP handler functions for session management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from agentic_rpg.api.dependencies import get_current_player, get_state_manager
from agentic_rpg.models.api import (
    BeatSummary,
    CharacterSummary,
    DeleteResponse,
    HistoryResponse,
    InventoryResponse,
    LocationSummary,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionSummary,
    StateSummaryResponse,
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


# ---------------------------------------------------------------------------
# Game state sub-endpoints
# ---------------------------------------------------------------------------


@router.get("/sessions/{session_id}/state")
async def get_state_summary(
    session_id: UUID,
    player_id: UUID = Depends(get_current_player),
    state_manager: StateManager = Depends(get_state_manager),
) -> StateSummaryResponse:
    """Get a lightweight summary of the current game state."""
    game_state = await state_manager.load_game_state(session_id)
    if game_state is None:
        raise HTTPException(status_code=404, detail={"error": "session_not_found"})

    char = game_state.character
    character_summary = CharacterSummary(
        name=char.name,
        profession=char.profession,
        level=char.level,
        health=char.stats.get("health", 0.0),
        max_health=char.stats.get("max_health", 0.0),
    )

    # Build location summary from current location
    loc_id = game_state.world.current_location_id
    loc = game_state.world.locations.get(loc_id)
    if loc:
        location_summary = LocationSummary(
            id=loc.id,
            name=loc.name,
            description=loc.description,
            connections=loc.connections,
        )
    else:
        location_summary = LocationSummary(
            id=loc_id, name=loc_id, description="", connections=[]
        )

    # Build active beat summary
    story_beat = None
    if game_state.story.outline and game_state.story.outline.beats:
        idx = game_state.story.active_beat_index
        if 0 <= idx < len(game_state.story.outline.beats):
            beat = game_state.story.outline.beats[idx]
            story_beat = BeatSummary(
                summary=beat.summary,
                location=beat.location,
                status=beat.status.value,
            )

    return StateSummaryResponse(
        character=character_summary,
        location=location_summary,
        story_beat=story_beat,
    )


@router.get("/sessions/{session_id}/inventory")
async def get_inventory(
    session_id: UUID,
    player_id: UUID = Depends(get_current_player),
    state_manager: StateManager = Depends(get_state_manager),
) -> InventoryResponse:
    """Get the character's inventory for a session."""
    game_state = await state_manager.load_game_state(session_id)
    if game_state is None:
        raise HTTPException(status_code=404, detail={"error": "session_not_found"})

    return InventoryResponse(
        items=game_state.inventory.items,
        equipment=game_state.inventory.equipment,
    )


@router.get("/sessions/{session_id}/history")
async def get_history(
    session_id: UUID,
    limit: int = 50,
    offset: int = 0,
    player_id: UUID = Depends(get_current_player),
    state_manager: StateManager = Depends(get_state_manager),
) -> HistoryResponse:
    """Get paginated conversation history for a session."""
    game_state = await state_manager.load_game_state(session_id)
    if game_state is None:
        raise HTTPException(status_code=404, detail={"error": "session_not_found"})

    history = game_state.conversation.history
    total = len(history)
    paginated = history[offset : offset + limit]

    return HistoryResponse(messages=paginated, total=total)

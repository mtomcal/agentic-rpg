# API Layer Specification

## Overview

The API layer is the HTTP and WebSocket server built with **FastAPI** that sits between the frontend client and the game engine. It handles session management, routes player actions to the agent, and pushes real-time updates to the client over WebSockets. FastAPI provides automatic request validation via Pydantic, built-in OpenAPI documentation, and native async support.

## Transport

### HTTP

Used for request/response operations:

- Creating new game sessions
- Loading existing sessions
- Getting game state
- Character creation
- Session management (list, delete, etc.)

### WebSocket

Used for real-time bidirectional communication:

- Sending player actions (text input)
- Receiving agent responses (narrative text, streamed)
- Receiving game state updates (events pushed to client)
- Connection lifecycle (connect, heartbeat, disconnect)

Each active game session has one WebSocket connection. The client connects when they enter a game and disconnects when they leave.

## HTTP Endpoints

All endpoints are defined as FastAPI route handlers with Pydantic request/response models. FastAPI automatically validates inputs and generates OpenAPI documentation.

### Session Management

**POST /api/v1/sessions**
Create a new game session.
- Request: `SessionCreateRequest { genre: str, character: CharacterCreate { name, profession, background } }`
- Response: `SessionCreateResponse { session_id: str, game_state: GameState }`
- Side effects: Creates character, generates story outline, initializes world

```python
@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(
    request: SessionCreateRequest,
    state_manager: StateManager = Depends(get_state_manager),
    player: Player = Depends(get_current_player),
) -> SessionCreateResponse:
    ...
```

**GET /api/v1/sessions**
List the player's sessions.
- Response: `SessionListResponse { sessions: list[SessionSummary] }`

**GET /api/v1/sessions/{session_id}**
Get full game state for a session.
- Response: `SessionDetailResponse { game_state: GameState }`

**DELETE /api/v1/sessions/{session_id}**
Delete a session.
- Response: `DeleteResponse { success: bool }`

### Game State

**GET /api/v1/sessions/{session_id}/state**
Get current game state summary (lighter than full state).
- Response: `StateSummaryResponse { character: CharacterSummary, location: LocationSummary, story_beat: BeatSummary }`

**GET /api/v1/sessions/{session_id}/inventory**
Get current inventory.
- Response: `InventoryResponse { items: list[Item], equipment: Equipment }`

**GET /api/v1/sessions/{session_id}/history**
Get conversation history.
- Query params: `limit: int`, `offset: int`
- Response: `HistoryResponse { messages: list[Message], total: int }`

### Health / Meta

**GET /api/health**
Health check.
- Response: `HealthResponse { status: str, version: str }`

## Dependency Injection

FastAPI's dependency injection system replaces manual constructor injection. Dependencies are declared as function parameters with `Depends()`:

```python
from fastapi import Depends

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def get_state_manager(db: AsyncSession = Depends(get_db)) -> StateManager:
    return StateManager(db=db)

async def get_current_player(
    player_id: str = Header(alias="X-Player-ID"),
) -> Player:
    ...
```

Dependencies are composable — `get_state_manager` depends on `get_db`, and FastAPI resolves the chain automatically.

## WebSocket Protocol

### Connection

The client connects to `ws://host/api/v1/sessions/{session_id}/ws`.

```python
@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    state_manager: StateManager = Depends(get_state_manager),
):
    await websocket.accept()
    ...
```

On connection:
1. Server validates the session ID exists and is active
2. Server sends a `connected` message with the current game state summary
3. The connection is registered in the WebSocket hub for this session

On disconnect:
1. The connection is removed from the hub
2. No game state changes — the session remains active

### Message Format

All WebSocket messages are JSON with a `type` field:

```json
{
  "type": "message_type",
  "data": { ... },
  "timestamp": "ISO 8601"
}
```

Messages are validated using Pydantic models:

```python
class WSMessage(BaseModel):
    type: str
    data: dict
    timestamp: datetime

class PlayerAction(BaseModel):
    type: Literal["player_action"]
    data: PlayerActionData

class PlayerActionData(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
```

### Client → Server Messages

**player_action**
```json
{
  "type": "player_action",
  "data": {
    "text": "I walk north toward the cave"
  }
}
```

The server routes this to the agent system, which processes it and emits responses.

### Server → Client Messages

**agent_response**
Narrative text from the agent. May be streamed in chunks.
```json
{
  "type": "agent_response",
  "data": {
    "text": "You approach the cave entrance...",
    "is_complete": false
  }
}
```

When `is_complete: true`, the agent has finished responding to this action.

**state_update**
A game state change occurred (event-driven).
```json
{
  "type": "state_update",
  "data": {
    "event_type": "character.stat_changed",
    "changes": {
      "character.stats.health": { "old": 100, "new": 85 }
    }
  }
}
```

> **Status:** Not yet implemented. State updates are not currently pushed to the client via WebSocket.

**error**
Something went wrong.
```json
{
  "type": "error",
  "data": {
    "code": "agent_error",
    "message": "Failed to process action"
  }
}
```

**connected**
Sent on initial connection.
```json
{
  "type": "connected",
  "data": {
    "session_id": "...",
    "character": { "name": "...", "profession": "...", "level": 1 },
    "location": { "id": "...", "name": "...", "description": "..." }
  }
}
```

**heartbeat**
Keep-alive ping/pong. Server sends a ping every 30 seconds. Client must respond with a pong. If no pong within 10 seconds, the server closes the connection.

> **Status:** Not yet implemented. Heartbeat ping/pong is planned but not yet active.

## Response Streaming

> **Status:** Not yet implemented. Agent responses are currently sent as a single complete message, not streamed in chunks.

Agent responses can be long. The server streams the response to the client in chunks as the LLM generates tokens:

1. Client sends `player_action`
2. Server begins agent processing
3. As the LLM generates text, server sends `agent_response` messages with `is_complete: false`
4. When the LLM finishes, server sends a final `agent_response` with `is_complete: true`
5. Any state changes that occurred during processing are sent as `state_update` messages after the response completes

The client should render text as it arrives (typewriter effect or progressive display).

FastAPI's WebSocket support handles this naturally — the server `await`s chunks from the LLM and sends each via `websocket.send_json()`.

## Authentication

For now, authentication is simple:

- Each client gets a player ID (could be a cookie, local storage token, or simple API key)
- The player ID is sent with each request/connection (via `X-Player-ID` header)
- Sessions are scoped to a player ID — you can only access your own sessions
- FastAPI dependency injection extracts and validates the player ID

This is intentionally minimal. A full auth system (OAuth, accounts, etc.) is a future extension.

## Rate Limiting

- Player actions: Max 1 action per second per session (natural rate limit — agent must finish before next action)
- Session creation: Max 10 sessions per player
- API requests: Standard rate limiting (100 req/min per player)

Rate limiting can be implemented via FastAPI middleware or a library like `slowapi`.

## Error Handling

FastAPI automatically returns validation errors for invalid request bodies (422 Unprocessable Entity). For application-level errors, all HTTP errors return:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable message"
  }
}
```

Implemented via FastAPI exception handlers:

```python
class GameError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

@app.exception_handler(GameError)
async def game_error_handler(request: Request, exc: GameError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
```

**Implementation note:** The current implementation uses `HTTPException(detail={"error": "message"})` for most errors, which produces `{"detail": {"error": "message"}}`. The structured `GameError` exception handler described above is planned but not yet fully implemented.

Standard error codes:
- `session_not_found` — Session ID doesn't exist
- `session_not_active` — Session is paused/completed/abandoned
- `invalid_request` — Request body validation failed
- `agent_error` — Agent processing failed
- `rate_limited` — Too many requests
- `internal_error` — Unexpected server error

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: Available at `/docs` — interactive API explorer
- **ReDoc**: Available at `/redoc` — clean API reference
- **OpenAPI JSON**: Available at `/openapi.json` — machine-readable spec

All documentation is generated from the Pydantic models, route decorators, and docstrings. No manual OpenAPI spec maintenance needed.

## Future Extensions

- **API versioning**: `/api/v2/` with breaking changes, using FastAPI routers
- **OAuth authentication**: Google, GitHub, etc. via `authlib` or FastAPI security utilities
- **Admin endpoints**: View all sessions, debug tools, metrics
- **Webhook support**: Notify external services of game events
- **GraphQL**: Alternative query interface via `strawberry-graphql` with FastAPI integration

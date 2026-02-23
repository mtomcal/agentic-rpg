# API Layer Specification

## Overview

The API layer is the HTTP and WebSocket server that sits between the frontend client and the game engine. It handles session management, routes player actions to the agent, and pushes real-time updates to the client over WebSockets.

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

### Session Management

**POST /api/v1/sessions**
Create a new game session.
- Request: `{ genre: string, character: { name, profession, background } }`
- Response: `{ session_id: string, game_state: GameState }`
- Side effects: Creates character, generates story outline, initializes world

**GET /api/v1/sessions**
List the player's sessions.
- Response: `{ sessions: [{ id, character_name, genre, status, updated_at }] }`

**GET /api/v1/sessions/:id**
Get full game state for a session.
- Response: `{ game_state: GameState }`

**DELETE /api/v1/sessions/:id**
Delete a session.
- Response: `{ success: boolean }`

### Game State

**GET /api/v1/sessions/:id/state**
Get current game state summary (lighter than full state).
- Response: `{ character: CharacterSummary, location: LocationSummary, story_beat: BeatSummary }`

**GET /api/v1/sessions/:id/inventory**
Get current inventory.
- Response: `{ items: Item[], equipment: Equipment }`

**GET /api/v1/sessions/:id/history**
Get conversation history.
- Query params: `limit`, `offset`
- Response: `{ messages: Message[], total: int }`

### Health / Meta

**GET /api/health**
Health check.
- Response: `{ status: "ok", version: string }`

## WebSocket Protocol

### Connection

The client connects to `ws://host/api/v1/sessions/:id/ws`.

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
    "character": { ... },
    "location": { ... }
  }
}
```

**heartbeat**
Keep-alive ping/pong. Server sends a ping every 30 seconds. Client must respond with a pong. If no pong within 10 seconds, the server closes the connection.

## Response Streaming

Agent responses can be long. The server streams the response to the client in chunks as the LLM generates tokens:

1. Client sends `player_action`
2. Server begins agent processing
3. As the LLM generates text, server sends `agent_response` messages with `is_complete: false`
4. When the LLM finishes, server sends a final `agent_response` with `is_complete: true`
5. Any state changes that occurred during processing are sent as `state_update` messages after the response completes

The client should render text as it arrives (typewriter effect or progressive display).

## Authentication

For now, authentication is simple:

- Each client gets a player ID (could be a cookie, local storage token, or simple API key)
- The player ID is sent with each request/connection
- Sessions are scoped to a player ID — you can only access your own sessions

This is intentionally minimal. A full auth system (OAuth, accounts, etc.) is a future extension.

## Rate Limiting

- Player actions: Max 1 action per second per session (natural rate limit — agent must finish before next action)
- Session creation: Max 10 sessions per player
- API requests: Standard rate limiting (100 req/min per player)

## Error Handling

All HTTP errors return:
```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable message"
  }
}
```

Standard error codes:
- `session_not_found` — Session ID doesn't exist
- `session_not_active` — Session is paused/completed/abandoned
- `invalid_request` — Request body validation failed
- `agent_error` — Agent processing failed
- `rate_limited` — Too many requests
- `internal_error` — Unexpected server error

## Future Extensions

- **API versioning**: `/api/v2/` with breaking changes
- **OAuth authentication**: Google, GitHub, etc.
- **Admin endpoints**: View all sessions, debug tools, metrics
- **Webhook support**: Notify external services of game events
- **GraphQL**: Alternative query interface for complex state queries

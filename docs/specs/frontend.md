# Frontend Specification

## Overview

The frontend is a browser-based client that presents the game to the player. It handles character creation, displays narrative text, shows game state (stats, inventory, map), and sends player actions to the server. It connects via HTTP for initial data loading and WebSocket for real-time gameplay.

## Screens

### Home Screen

- List of existing game sessions (with character name, genre, last played)
- "New Game" button to create a new session
- Delete session option

### Character Creation

- Genre/setting selection (or free-text description)
- Character name input
- Profession/class selection (genre-appropriate options)
- Optional background/backstory text
- "Start Game" button — calls the session creation API, then navigates to the game screen

### Game Screen

The primary play interface. Split into regions:

**Narrative Panel** (main area)
- Displays agent responses as they stream in (typewriter-style or progressive reveal)
- Shows the conversation history (scrollable)
- Player input field at the bottom (text input + send button)

**Character Panel** (sidebar or collapsible)
- Character name, profession
- Stats (health bar, energy bar, money, level)
- Active status effects
- Equipment summary

**Inventory Panel** (sidebar tab or modal)
- List of items with icons/descriptions
- Equip/unequip/use actions
- Item details on click

**Location Panel** (sidebar tab or header)
- Current location name and brief description
- List of connected locations (clickable to move)
- Minimap or location list (future)

The layout should be responsive but primarily designed for desktop. Mobile is a future consideration.

## State Management

The client maintains local state for:

- **Game state**: Mirrored from the server, updated via WebSocket `state_update` messages
- **UI state**: Which panel is open, input field contents, scroll positions
- **Connection state**: WebSocket status (connected, reconnecting, disconnected)

State management should be simple and lightweight. A small state store (like Zustand) is sufficient. The server is the source of truth — the client never makes optimistic updates to game state.

### State Sync

1. On entering a game session, load full state via HTTP
2. Open WebSocket connection
3. Receive `state_update` events and patch local state
4. If the WebSocket disconnects and reconnects, re-fetch full state via HTTP to re-sync

## Player Input

The player types text commands into an input field. Examples:

- "I walk north toward the cave"
- "Search the room for hidden passages"
- "Attack the guard with my sword"
- "Talk to the merchant about the missing shipment"

The input is sent as a `player_action` WebSocket message. While the agent is processing, the input field is disabled (or shows a "thinking" indicator).

Some actions can also be triggered by clicking UI elements:
- Clicking a connected location → sends a move action
- Clicking "Use" on an inventory item → sends a use item action
- These are convenience shortcuts that generate the same `player_action` messages

## Real-Time Updates

The client receives and handles these WebSocket messages:

- **agent_response**: Append text to the narrative panel. If streaming, show text as it arrives.
- **state_update**: Patch the local game state. UI reactively updates (health bar changes, inventory updates, location changes, etc.)
- **error**: Show an error notification to the player.
- **heartbeat**: Respond with pong to keep the connection alive.

## Error Handling

- **WebSocket disconnect**: Show a "reconnecting" indicator. Auto-reconnect with exponential backoff. On reconnect, re-sync state.
- **API errors**: Show user-friendly error messages. Never show raw error payloads.
- **Agent timeout**: If no response within 30 seconds, show "The game master is thinking..." and allow retry.
- **Session not found**: Redirect to home screen with a message.

## Theming

The UI should support a dark theme by default (fits the RPG aesthetic). The visual style should be genre-neutral — the narrative text provides the flavor, not the UI chrome.

Minimal UI, maximum narrative focus. The game is a text-heavy experience with supporting UI panels, not a graphical RPG.

## Future Extensions

- **Rich text / markdown rendering**: Bold, italic, headers in agent responses
- **Sound effects**: Ambient audio based on location
- **Minimap**: Visual map generated from location graph
- **Character portrait**: AI-generated character art
- **Mobile layout**: Responsive design for phone/tablet
- **Accessibility**: Screen reader support, keyboard navigation, high contrast mode

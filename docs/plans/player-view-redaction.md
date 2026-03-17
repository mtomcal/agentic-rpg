# Plan: Player View Redaction (No Spoilers)

## Problem

The full story outline (all beats with summaries) is sent to the frontend in `state_snapshot` and `connected` WebSocket messages. Players can see future plot points, boss identities, and story resolution before reaching them. LLM-as-judge flagged this as a critical `outline_no_spoilers` failure.

## Solution

Add a `to_player_view()` method on `StoryState` that redacts `planned` beats before serialization. Apply it at every backend→frontend boundary.

## Implementation Steps

### 1. Backend: Add `StoryState.to_player_view()` method

**File**: `backend/src/agentic_rpg/models/story.py`

- Add `to_player_view()` method to `StoryState`
- Planned beats get summary replaced with `"???"` and detail lists emptied
- All other beat statuses pass through unchanged
- Returns a new `StoryState` (no mutation)

### 2. Backend: Add `GameState.to_player_view()` method

**File**: `backend/src/agentic_rpg/models/game_state.py`

- Add `to_player_view()` that returns a copy with `story` replaced by `story.to_player_view()`
- This is the single call site for all serialization points

### 3. Backend: Apply redaction in WebSocket handler

**File**: `backend/src/agentic_rpg/api/websocket.py`

- In `_generate_opening()`: use `game_state.to_player_view()` when building `state_snapshot` data
- In `connected` message: use `game_state.to_player_view()`
- In action response handler: use `game_state.to_player_view()` when building `state_snapshot`

### 4. Backend: Apply redaction in REST endpoints

**File**: `backend/src/agentic_rpg/api/handlers.py` (or wherever session detail endpoint lives)

- `GET /sessions/{id}` response: use `game_state.to_player_view()`
- `GET /sessions/{id}/state` already only returns active beat — verify no leak

### 5. Frontend: Update StoryPanel for redacted beats

**File**: `frontend/components/StoryPanel.tsx`

- For beats with summary `"???"`: show lock icon instead of planned circle
- Style redacted beats distinctly (dimmed, no hover)

### 6. Tests

**Backend tests** (TDD — write first):
- `test_story_state_to_player_view_redacts_planned_beats`
- `test_story_state_to_player_view_preserves_resolved_beats`
- `test_story_state_to_player_view_preserves_active_beat`
- `test_story_state_to_player_view_handles_no_outline`
- `test_game_state_to_player_view_delegates_to_story`
- `test_websocket_sends_redacted_state` (verify planned beats are `"???"` in WS messages)

**Frontend tests**:
- `test_story_panel_renders_redacted_beats_with_lock_icon`
- `test_story_panel_does_not_show_future_summaries`

### 7. Re-run LLM-as-judge evaluation

Verify `outline_no_spoilers` criterion now passes.

## Files Changed

| File | Change |
|------|--------|
| `backend/src/agentic_rpg/models/story.py` | Add `to_player_view()` |
| `backend/src/agentic_rpg/models/game_state.py` | Add `to_player_view()` |
| `backend/src/agentic_rpg/api/websocket.py` | Apply redaction at send points |
| `backend/src/agentic_rpg/api/handlers.py` | Apply redaction in REST responses |
| `frontend/components/StoryPanel.tsx` | Handle redacted beats |
| `docs/specs/story-engine.md` | Already updated with spec |
| `backend/tests/test_models/test_story.py` | Redaction unit tests |
| `frontend/__tests__/components/StoryPanel.test.tsx` | Redacted beat rendering tests |

## Not Changed

- Database schema (full outline still stored)
- Agent prompt assembly (agent still sees full outline)
- Story engine internals (generation, adaptation)
